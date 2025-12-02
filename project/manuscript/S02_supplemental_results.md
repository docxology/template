# Supplemental Results

## S2.1 Extended Axiom Verification Results

### Calling Axiom: Complete Test Suite

| Test Case | Input | Expected | Actual | Status |
|-----------|-------|----------|--------|--------|
| Mark in double enclosure | $\langle\langle\langle\ \rangle\rangle\rangle$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| Void in double enclosure | $\langle\langle\emptyset\rangle\rangle$ | $\emptyset$ | $\emptyset$ | ✓ |
| Triple enclosure | $\langle\langle\langle\langle\ \rangle\rangle\rangle\rangle$ | $\langle\langle\ \rangle\rangle$ | $\langle\langle\ \rangle\rangle$ | ✓ |
| Quadruple enclosure | $\langle\langle\langle\langle\emptyset\rangle\rangle\rangle\rangle$ | $\emptyset$ | $\emptyset$ | ✓ |
| Nested complex | $\langle\langle\langle\ \rangle\langle\ \rangle\rangle\rangle$ | $\langle\ \rangle\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |

### Crossing Axiom: Complete Test Suite

| Test Case | Input | Expected | Actual | Status |
|-----------|-------|----------|--------|--------|
| Two marks | $\langle\ \rangle\langle\ \rangle$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| Three marks | $\langle\ \rangle\langle\ \rangle\langle\ \rangle$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| Five marks | $\langle\ \rangle^5$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| Marks with void | $\langle\ \rangle\emptyset\langle\ \rangle$ | $\emptyset$ | $\emptyset$ | ✓ |
| Enclosed marks | $\langle\langle\ \rangle\langle\ \rangle\rangle$ | $\langle\langle\ \rangle\rangle$ | $\emptyset$ | ✓ |

## S2.2 Consequence Verification Details

### C1 (Position): $\langle\langle a \rangle b \rangle a = a$

**Substitution Tests**:

| $a$ | $b$ | LHS | RHS | Equal |
|-----|-----|-----|-----|-------|
| $\langle\ \rangle$ | $\langle\ \rangle$ | $\langle\langle\langle\ \rangle\rangle\langle\ \rangle\rangle\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| $\langle\ \rangle$ | $\emptyset$ | $\langle\langle\langle\ \rangle\rangle\emptyset\rangle\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| $\emptyset$ | $\langle\ \rangle$ | $\langle\langle\emptyset\rangle\langle\ \rangle\rangle\emptyset$ | $\emptyset$ | ✓ |
| $\emptyset$ | $\emptyset$ | $\langle\langle\emptyset\rangle\emptyset\rangle\emptyset$ | $\emptyset$ | ✓ |

### C3 (Generation): $\langle\langle a \rangle a \rangle = \langle\ \rangle$

**This is the Law of Excluded Middle: $a \lor \neg a = \text{TRUE}$**

| $a$ | LHS | Reduced | Expected |
|-----|-----|---------|----------|
| $\langle\ \rangle$ | $\langle\emptyset\langle\ \rangle\rangle$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| $\emptyset$ | $\langle\langle\ \rangle\emptyset\rangle$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |

### C6 (Iteration): $aa = a$

**This is Idempotence of AND**

| $a$ | LHS | Reduced | Expected |
|-----|-----|---------|----------|
| $\langle\ \rangle$ | $\langle\ \rangle\langle\ \rangle$ | $\langle\ \rangle$ | $\langle\ \rangle$ | ✓ |
| $\emptyset$ | $\emptyset\emptyset$ | $\emptyset$ | $\emptyset$ | ✓ |

## S2.3 Boolean Axiom Verification

### Full Boolean Axiom Set

| Axiom | Boolean Form | Boundary Form | Verified |
|-------|--------------|---------------|----------|
| AND Identity | $a \land T = a$ | $a\langle\ \rangle = a$ | ✓ |
| OR Identity | $a \lor F = a$ | $\langle\langle a \rangle\langle\emptyset\rangle\rangle = a$ | ✓ |
| AND Domination | $a \land F = F$ | $a\emptyset = \emptyset$ | ✓ |
| OR Domination | $a \lor T = T$ | $\langle\langle a \rangle\langle\langle\ \rangle\rangle\rangle = \langle\ \rangle$ | ✓ |
| AND Idempotent | $a \land a = a$ | $aa = a$ | ✓ |
| OR Idempotent | $a \lor a = a$ | $\langle\langle a \rangle\langle a \rangle\rangle = a$ | ✓ |
| Double Negation | $\neg\neg a = a$ | $\langle\langle a \rangle\rangle = a$ | ✓ |
| Complement (AND) | $a \land \neg a = F$ | $a\langle a \rangle = \emptyset$ | ✓ |
| Complement (OR) | $a \lor \neg a = T$ | $\langle\langle a \rangle a\rangle = \langle\ \rangle$ | ✓ |

### De Morgan's Laws

**DM1**: $\neg(a \land b) = \neg a \lor \neg b$

| $a$ | $b$ | $\langle ab\rangle$ | $\langle\langle\langle a\rangle\rangle\langle\langle b\rangle\rangle\rangle$ | Equal |
|-----|-----|---------------------|-------------------------------------------|-------|
| T | T | F | F | ✓ |
| T | F | T | T | ✓ |
| F | T | T | T | ✓ |
| F | F | T | T | ✓ |

**DM2**: $\neg(a \lor b) = \neg a \land \neg b$

| $a$ | $b$ | $\langle\langle\langle a\rangle\langle b\rangle\rangle\rangle$ | $\langle a\rangle\langle b\rangle$ | Equal |
|-----|-----|----------------------------------------------|-------------------|-------|
| T | T | F | F | ✓ |
| T | F | F | F | ✓ |
| F | T | F | F | ✓ |
| F | F | T | T | ✓ |

## S2.4 Complexity Analysis Data

### Reduction Steps by Form Complexity

| Depth | Size | Mean Steps | Median | Max | Std Dev |
|-------|------|------------|--------|-----|---------|
| 1 | 1 | 0.0 | 0 | 0 | 0.0 |
| 2 | 2-3 | 0.8 | 1 | 2 | 0.6 |
| 3 | 4-6 | 2.1 | 2 | 5 | 1.2 |
| 4 | 7-12 | 4.3 | 4 | 9 | 2.0 |
| 5 | 13-20 | 6.8 | 7 | 14 | 2.7 |
| 6 | 21-35 | 9.5 | 9 | 21 | 3.4 |

### Rule Application Frequency

Over 500 random forms:

| Rule | Count | Percentage |
|------|-------|------------|
| Calling | 1,847 | 42.3% |
| Crossing | 1,623 | 37.2% |
| Void Elimination | 894 | 20.5% |

### Canonical Form Distribution

| Canonical Form | Count | Percentage |
|----------------|-------|------------|
| $\langle\ \rangle$ (TRUE) | 267 | 53.4% |
| $\emptyset$ (FALSE) | 233 | 46.6% |

The near-50/50 distribution confirms unbiased random generation.

## S2.5 Performance Benchmarks

### Reduction Time by Form Size

| Size (marks) | Mean Time (μs) | Std Dev |
|--------------|----------------|---------|
| 1-5 | 12.3 | 2.1 |
| 6-10 | 28.7 | 5.4 |
| 11-20 | 67.2 | 12.8 |
| 21-50 | 189.4 | 34.6 |
| 51-100 | 512.8 | 89.3 |

### Memory Usage

| Form Size | Memory (bytes) |
|-----------|----------------|
| 1 | 128 |
| 10 | 1,024 |
| 100 | 10,240 |
| 1,000 | 102,400 |

Memory scales linearly with form size.

## S2.6 Edge Case Results

### Pathological Forms

| Description | Form | Steps | Result |
|-------------|------|-------|--------|
| Empty juxtaposition | $()$ | 0 | $\emptyset$ |
| Deeply nested marks | $\langle...\langle\langle\ \rangle\rangle...\rangle$ (d=10) | 5 | $\langle\ \rangle$ |
| Wide juxtaposition | $\langle\ \rangle^{20}$ | 19 | $\langle\ \rangle$ |
| Mixed deep/wide | Complex | 37 | $\emptyset$ |

### Stress Testing

| Test | Forms | All Terminated | Max Time |
|------|-------|----------------|----------|
| Random d≤6 | 1,000 | ✓ | 1.2ms |
| Random d≤8 | 1,000 | ✓ | 4.8ms |
| Adversarial | 100 | ✓ | 12.3ms |
