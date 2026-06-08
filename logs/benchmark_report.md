# Micromouse Benchmark Report

*Generated: 2026-06-08 14:41:11*

**Total runs:** 47


## FloodFill

Runs completed: 11
Goal success rate: 10/11

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 165.0909 | 170 | 46.0575 | 46 | 214 |
| final_path_length | 71 | 75 | 21.1471 | 22 | 96 |
| total_moves | 291.6364 | 305 | 86.9198 | 74 | 445 |
| total_turns | 134.5455 | 126 | 60.3645 | 43 | 287 |
| elapsed_seconds | 33.0382 | 34.223 | 11.6036 | 10.4261 | 47.0306 |
| replan_count | 126.8182 | 140 | 34.8506 | 41 | 163 |
| new_walls_found | 126.8182 | 140 | 34.8506 | 41 | 163 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 139.9091 | 138 | 72.2322 | 24 | 324 |
| turns | 63.3636 | 54 | 54.7655 | 13 | 224 |
| cells_visited | 119.0909 | 117 | 45.6431 | 23 | 209 |
| time_seconds | 17.2337 | 20.5764 | 6.6842 | 3.8183 | 24.2846 |
| walls_found | 94.3636 | 94 | 33.1641 | 22 | 144 |
| replan_count | 94.3636 | 94 | 33.1641 | 22 | 144 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 87.5455 | 102 | 30.985 | 28 | 120 |
| turns | 41.9091 | 32 | 17.9469 | 17 | 70 |
| cells_visited | 44.0909 | 41 | 28.891 | 3 | 86 |
| time_seconds | 10.4649 | 7.729 | 5.2533 | 4.455 | 18.8277 |
| walls_found | 32.4545 | 20 | 23.4494 | 2 | 69 |
| replan_count | 32.4545 | 20 | 23.4494 | 2 | 69 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 64.1818 | 70 | 25.9531 | 15 | 96 |
| turns | 29.2727 | 29 | 12.0672 | 5 | 44 |
| cells_visited | 0.9091 | 0 | 2.7002 | 0 | 9 |
| time_seconds | 5.3396 | 4.1103 | 3.2202 | 0.7265 | 11.2463 |
| walls_found | 0 | 0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0 | 0.0 | 0 | 0 |

## IncrementalAStar

Runs completed: 36
Goal success rate: 32/36

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 121.9722 | 133.0 | 70.3365 | 15 | 216 |
| final_path_length | 53.4444 | 58.0 | 25.9025 | 14 | 94 |
| total_moves | 213.5278 | 268.0 | 104.2778 | 42 | 326 |
| total_turns | 110.75 | 121.0 | 59.0014 | 7 | 206 |
| elapsed_seconds | 31.9977 | 20.913 | 29.0271 | 6.2211 | 166.652 |
| replan_count | 55.1667 | 62.0 | 37.0448 | 0 | 135 |
| new_walls_found | 92.3056 | 99.0 | 54.8358 | 1 | 178 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 98.2222 | 112.0 | 60.4025 | 14 | 214 |
| turns | 50.6389 | 51.0 | 35.6668 | 1 | 136 |
| cells_visited | 85.5833 | 104.0 | 47.4645 | 14 | 190 |
| time_seconds | 15.0012 | 11.5846 | 12.3013 | 3.0028 | 62.9054 |
| walls_found | 67.5 | 83.0 | 39.9124 | 1 | 172 |
| replan_count | 41.2222 | 51.0 | 27.3998 | 0 | 129 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 67.8333 | 74.0 | 35.5725 | 14 | 118 |
| turns | 36.0556 | 33.0 | 22.2312 | 3 | 82 |
| cells_visited | 34.8611 | 28.0 | 32.0376 | 0 | 88 |
| time_seconds | 9.9783 | 6.9046 | 10.4972 | 1.6133 | 59.9172 |
| walls_found | 24.8056 | 16.0 | 24.582 | 0 | 67 |
| replan_count | 13.9444 | 10.0 | 14.84 | 0 | 42 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 47.4722 | 56.0 | 26.9194 | 13 | 94 |
| turns | 24.0556 | 27.0 | 14.2947 | 3 | 46 |
| cells_visited | 0.5278 | 0.0 | 1.483 | 0 | 6 |
| time_seconds | 7.0182 | 4.013 | 9.2575 | 0.7188 | 43.8294 |
| walls_found | 0 | 0.0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0.0 | 0.0 | 0 | 0 |