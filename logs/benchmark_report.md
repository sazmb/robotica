# Micromouse Benchmark Report

*Generated: 2026-06-08 08:58:28*

**Total runs:** 39


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

Runs completed: 28
Goal success rate: 24/28

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 134.5 | 168.5 | 68.9796 | 16 | 216 |
| final_path_length | 54.2857 | 58.0 | 22.6272 | 14 | 94 |
| total_moves | 223.9643 | 268.0 | 94.0608 | 45 | 326 |
| total_turns | 116.8929 | 121.0 | 52.2326 | 15 | 206 |
| elapsed_seconds | 26.9868 | 20.1704 | 17.3 | 6.2211 | 86.6162 |
| replan_count | 61.6071 | 66.0 | 36.4004 | 2 | 135 |
| new_walls_found | 102.8929 | 126.0 | 52.5233 | 7 | 178 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 107.7857 | 112.0 | 60.0841 | 15 | 214 |
| turns | 56.8214 | 51.0 | 35.7978 | 5 | 136 |
| cells_visited | 92.8571 | 109.5 | 45.8352 | 15 | 190 |
| time_seconds | 12.8979 | 10.2398 | 8.3142 | 3.3266 | 37.6369 |
| walls_found | 74.0357 | 87.0 | 37.644 | 6 | 172 |
| replan_count | 45.2857 | 51.0 | 26.6303 | 2 | 129 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 69.5714 | 74.0 | 32.6036 | 14 | 118 |
| turns | 36.5 | 33.0 | 20.2128 | 4 | 82 |
| cells_visited | 39.9643 | 32.5 | 34.0169 | 0 | 88 |
| time_seconds | 8.2043 | 6.8983 | 5.9434 | 1.6133 | 31.1174 |
| walls_found | 28.8571 | 23.5 | 26.1898 | 0 | 67 |
| replan_count | 16.3214 | 12.0 | 15.8979 | 0 | 42 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 46.6071 | 56.0 | 24.1129 | 13 | 94 |
| turns | 23.5714 | 27.0 | 11.8116 | 4 | 46 |
| cells_visited | 0.6786 | 0.0 | 1.6567 | 0 | 6 |
| time_seconds | 5.8846 | 3.6921 | 7.4006 | 0.7188 | 38.8135 |
| walls_found | 0 | 0.0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0.0 | 0.0 | 0 | 0 |