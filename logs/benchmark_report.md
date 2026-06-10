# Micromouse Benchmark Report

*Generated: 2026-06-10 10:54:36*

**Total runs:** 40


## FloodFill

Runs completed: 20
Goal success rate: 20/20

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 143.3 | 145.0 | 46.694 | 66 | 224 |
| final_path_length | 62.3 | 62.0 | 19.7567 | 27 | 104 |
| total_moves | 263.2 | 241.0 | 80.9929 | 123 | 424 |
| total_turns | 122.9 | 105.5 | 70.8645 | 38 | 296 |
| elapsed_seconds | 25.8127 | 23.4175 | 8.9754 | 11.9264 | 43.8297 |
| replan_count | 104.95 | 117.5 | 37.0866 | 39 | 157 |
| new_walls_found | 104.95 | 117.5 | 37.0866 | 39 | 157 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 116.8 | 115.5 | 48.9969 | 44 | 217 |
| turns | 52.75 | 41.0 | 36.5814 | 12 | 134 |
| cells_visited | 100.75 | 98.5 | 37.1411 | 43 | 162 |
| time_seconds | 12.9595 | 12.5545 | 5.7139 | 5.0842 | 24.4515 |
| walls_found | 77.7 | 68.0 | 30.2309 | 30 | 133 |
| replan_count | 77.7 | 68.0 | 30.2309 | 30 | 133 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 84.1 | 80.0 | 33.868 | 35 | 154 |
| turns | 43.85 | 34.5 | 31.8438 | 12 | 125 |
| cells_visited | 41.55 | 31.0 | 28.0516 | 10 | 100 |
| time_seconds | 9.2894 | 8.249 | 4.2917 | 3.7314 | 18.8836 |
| walls_found | 27.25 | 21.0 | 21.3711 | 1 | 65 |
| replan_count | 27.25 | 21.0 | 21.3711 | 1 | 65 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 62.3 | 62.0 | 19.7567 | 27 | 104 |
| turns | 26.3 | 23.0 | 15.4344 | 8 | 67 |
| cells_visited | 0 | 0.0 | 0.0 | 0 | 0 |
| time_seconds | 3.5638 | 3.4345 | 1.2293 | 1.4932 | 5.8775 |
| walls_found | 0 | 0.0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0.0 | 0.0 | 0 | 0 |

### Results by Maze Typology
| Typology | Runs | Success | Avg Moves | Avg Time (s) |
| --- | --- | --- | --- | --- |
| competition | 8 | 8/8 | 315.1 | 32.0310 |
| dead_end | 3 | 3/3 | 277.3 | 28.1022 |
| multiple_path | 3 | 3/3 | 269.3 | 24.0905 |
| open_area | 3 | 3/3 | 139.7 | 12.9325 |
| symmetric | 3 | 3/3 | 228.0 | 21.5435 |

## IncrementalAStar

Runs completed: 20
Goal success rate: 20/20

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 144.6 | 157.0 | 47.5211 | 69 | 212 |
| final_path_length | 62.65 | 63.5 | 20.1423 | 27 | 104 |
| total_moves | 267.55 | 283.0 | 79.6231 | 123 | 410 |
| total_turns | 124.3 | 96.5 | 65.4636 | 38 | 290 |
| elapsed_seconds | 24.6325 | 25.2402 | 7.8172 | 11.5582 | 40.853 |
| replan_count | 68.05 | 69.0 | 29.3553 | 27 | 129 |
| new_walls_found | 106.6 | 114.5 | 40.0492 | 38 | 174 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 125.05 | 123.0 | 49.3169 | 60 | 211 |
| turns | 57.8 | 42.0 | 37.1747 | 22 | 158 |
| cells_visited | 107.15 | 104.0 | 38.5804 | 57 | 183 |
| time_seconds | 12.5365 | 12.1723 | 5.2022 | 6.1194 | 22.1876 |
| walls_found | 82.65 | 83.0 | 33.73 | 33 | 156 |
| replan_count | 54 | 54.0 | 25.4662 | 25 | 117 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 79.85 | 68.0 | 34.2411 | 35 | 156 |
| turns | 40.4 | 31.5 | 29.0125 | 8 | 107 |
| cells_visited | 36.45 | 31.0 | 28.7759 | 0 | 95 |
| time_seconds | 8.505 | 7.2276 | 3.9276 | 3.6685 | 17.1795 |
| walls_found | 23.95 | 17.0 | 20.5567 | 1 | 60 |
| replan_count | 14.05 | 10.5 | 12.7753 | 0 | 41 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 62.65 | 63.5 | 20.1423 | 27 | 104 |
| turns | 26.1 | 25.0 | 15.2795 | 8 | 69 |
| cells_visited | 0 | 0.0 | 0.0 | 0 | 0 |
| time_seconds | 3.5911 | 3.4421 | 1.2084 | 1.6392 | 5.9171 |
| walls_found | 0 | 0.0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0.0 | 0.0 | 0 | 0 |

### Results by Maze Typology
| Typology | Runs | Success | Avg Moves | Avg Time (s) |
| --- | --- | --- | --- | --- |
| competition | 8 | 8/8 | 301.8 | 28.8630 |
| dead_end | 3 | 3/3 | 254.0 | 23.7199 |
| multiple_path | 3 | 3/3 | 327.3 | 28.2366 |
| open_area | 3 | 3/3 | 153.0 | 13.8391 |
| symmetric | 3 | 3/3 | 244.7 | 21.4532 |