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
        # Applies to every compiled package and component, including library SRTs.
        ghcOptions = [ "-fobject-determinism" ];
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
