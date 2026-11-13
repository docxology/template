let
  system = "x86_64-linux";
  upstream = builtins.getFlake
    "git+https://github.com/lierdakil/pandoc-crossref?rev=e6c2ae3418dcf63f974802f8b7c105ebc299706c";
  haskellNix = upstream.inputs.haskellNix;
  pkgs = import upstream.inputs.nixpkgs {
    inherit system;
    overlays = [ haskellNix.overlay ];
    inherit (haskellNix) config;
  };
  stockCompiler = pkgs.haskell-nix.compiler.ghc9122;
  cacheSource = pkgs.applyPatches {
    name = "ghc-9.12.2-stable-package-cache-source";
    src = stockCompiler.src;
    patches = [ ./native-document-ghc-pkg-cache-order.patch ];
  };
  cacheUtility = pkgs.runCommand "ghc-pkg-9.12.2-stable-package-cache" {
    nativeBuildInputs = [ stockCompiler ];
  } ''
    mkdir -p "$out/bin" "$out/nix-support"
    cp ${cacheSource}/utils/ghc-pkg/Main.hs Main.hs
    ${stockCompiler}/bin/ghc --make Main.hs -o "$out/bin/ghc-pkg" \
      -XGHC2021 -XCPP -O2 -fobject-determinism -threaded -rtsopts -j"$NIX_BUILD_CORES" \
      -hide-all-packages -package base -package directory -package process \
      -package containers -package filepath -package Cabal -package Cabal-syntax \
      -package binary -package ghc-boot -package bytestring -package unix
    cp Main.hs "$out/nix-support/ghc-pkg-Main.hs"
    cp ${./native-document-ghc-pkg-cache-order.patch} "$out/nix-support/source.patch"
  '';
  correctedCompiler = pkgs.haskell-nix.haskellLib.makeCompilerDeps (stockCompiler.overrideAttrs (_old: {
    phases = [ "buildPhase" ];
    nativeBuildInputs = [ pkgs.xorg.lndir ];
    buildInputs = [];
    patches = [];
    buildPhase = ''
      mkdir -p "$out" "$doc" "$generated"
      lndir -silent ${stockCompiler} "$out"
      lndir -silent ${stockCompiler.doc} "$doc"
      lndir -silent ${stockCompiler.generated} "$generated"
      test -f "$out/lib/ghc-9.12.2/bin/ghc-pkg"
      rm "$out/lib/ghc-9.12.2/bin/ghc-pkg"
      cp ${cacheUtility}/bin/ghc-pkg "$out/lib/ghc-9.12.2/bin/ghc-pkg"
      for name in ghc-pkg ghc-pkg-9.12.2; do
        rm "$out/bin/$name"
        ln -s ../lib/ghc-9.12.2/bin/ghc-pkg "$out/bin/$name"
      done
      rm -f "$out/lib/ghc-9.12.2/lib/package.conf.d/package.cache.lock"
      "$out/bin/ghc-pkg" --global-package-db="$out/lib/ghc-9.12.2/lib/package.conf.d" recache
    '';
  }));
  project = pkgs.haskell-nix.cabalProject' {
    src = upstream.outPath;
    compiler-nix-name = "ghc9122";
    index-state = "2026-09-06T18:04:17Z";
    cabalProject = builtins.readFile "${upstream.outPath}/cabal.project";
    cabalProjectFreeze = builtins.readFile ./native-document-build.freeze;
    cabalProjectLocal = ''
      package pandoc-crossref
        flags: +enable_flaky_tests
    '';
    modules = [
      ({ lib, ... }: {
        doHaddock = lib.mkForce false;
        ghc.package = lib.mkForce correctedCompiler;
        # Applies to every compiled package and component, including library SRTs.
        ghcOptions = [ "-fobject-determinism" ];
        packages.pandoc-cli.components.exes.pandoc.keepConfigFiles = true;
        packages.pandoc-crossref.components.exes.pandoc-crossref.keepConfigFiles = true;
      })
    ];
  };
  pandoc = project.hsPkgs.pandoc-cli.components.exes.pandoc;
  crossref = project.hsPkgs.pandoc-crossref.components.exes.pandoc-crossref;
  provider = pkgs.symlinkJoin {
    name = "pandoc-with-crossref";
    paths = [ crossref pandoc ];
  };
in {
  inherit pandoc crossref provider;
  compiler = project.pkg-set.config.ghc.package;
  plan = project.plan-nix;
  resolvedFreeze = project.plan-nix.freeze;
  runtimeClosure = pkgs.closureInfo { rootPaths = [ provider ]; };
}
