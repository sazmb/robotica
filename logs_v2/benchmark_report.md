# Micromouse Benchmark Report

*Generated: 2026-06-10 09:20:36*

**Total runs:** 40


## FloodFill

Runs completed: 20
Goal success rate: 20/20

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 156.2 | 172.0 | 46.7756 | 77 | 231 |
| final_path_length | 63.1 | 62.5 | 20.1073 | 27 | 104 |
| total_moves | 288.5 | 310.5 | 88.2821 | 136 | 488 |
| total_turns | 138.35 | 117.5 | 80.4731 | 36 | 370 |
| elapsed_seconds | 26.666 | 22.8473 | 12.4137 | 9.7344 | 57.6406 |
| replan_count | 110.45 | 119.0 | 37.517 | 42 | 159 |
| new_walls_found | 110.45 | 119.0 | 37.517 | 42 | 159 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 116.8 | 115.5 | 48.9969 | 44 | 217 |
| turns | 52.75 | 41.0 | 36.5814 | 12 | 134 |
| cells_visited | 100.75 | 98.5 | 37.1411 | 43 | 162 |
| time_seconds | 13.076 | 12.1578 | 6.8034 | 3.8977 | 27.6437 |
| walls_found | 77.7 | 68.0 | 30.2309 | 30 | 133 |
| replan_count | 77.7 | 68.0 | 30.2309 | 30 | 133 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 108.6 | 98.0 | 38.2944 | 46 | 204 |
| turns | 59.65 | 50.0 | 40.1527 | 14 | 178 |
| cells_visited | 54.45 | 51.0 | 26.6922 | 11 | 107 |
| time_seconds | 11.063 | 9.2787 | 6.0814 | 4.3404 | 26.0905 |
| walls_found | 32.75 | 27.0 | 21.5159 | 4 | 71 |
| replan_count | 32.75 | 27.0 | 21.5159 | 4 | 71 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 63.1 | 62.5 | 20.1073 | 27 | 104 |
| turns | 25.95 | 23.0 | 15.2297 | 10 | 67 |
| cells_visited | 0 | 0.0 | 0.0 | 0 | 0 |
| time_seconds | 2.527 | 2.5308 | 0.9956 | 1.1582 | 4.7704 |
| walls_found | 0 | 0.0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0.0 | 0.0 | 0 | 0 |

### Results by Maze Typology
| Typology | Runs | Success | Avg Moves | Avg Time (s) |
| --- | --- | --- | --- | --- |
| competition | 8 | 8/8 | 337.9 | 29.2833 |
| dead_end | 3 | 3/3 | 312.7 | 27.3979 |
| multiple_path | 3 | 3/3 | 272.0 | 27.9362 |
| open_area | 3 | 3/3 | 162.3 | 13.7087 |
| symmetric | 3 | 3/3 | 275.3 | 30.6418 |

### Results by Algorithm Version
| Version | Runs | Success | Avg Moves | Avg Turns | Avg Time (s) | Avg Path Len |
| --- | --- | --- | --- | --- | --- | --- |
| v2 | 20 | 20/20 | 288.5 | 138.3 | 26.6660 | 63.1 |

## IncrementalAStar

Runs completed: 20
Goal success rate: 20/20

### Whole-run Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| visited_cells | 150.45 | 157.5 | 47.4868 | 76 | 217 |
| final_path_length | 61.8 | 61.0 | 19.5814 | 29 | 104 |
| total_moves | 269.8 | 283.5 | 81.6376 | 127 | 428 |
| total_turns | 126.6 | 100.5 | 68.0707 | 46 | 318 |
| elapsed_seconds | 24.216 | 24.3905 | 9.3289 | 8.2153 | 41.6409 |
| replan_count | 70.2 | 72.0 | 29.9185 | 28 | 129 |
| new_walls_found | 110.8 | 120.5 | 41.1373 | 41 | 175 |

### Phase1 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 125.05 | 123.0 | 49.3169 | 60 | 211 |
| turns | 57.8 | 42.0 | 37.1747 | 22 | 158 |
| cells_visited | 107.15 | 104.0 | 38.5804 | 57 | 183 |
| time_seconds | 13.2567 | 12.7578 | 6.0371 | 3.7335 | 22.8816 |
| walls_found | 82.65 | 83.0 | 33.73 | 33 | 156 |
| replan_count | 54 | 54.0 | 25.4662 | 25 | 117 |

### Phase2 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 82.95 | 75.0 | 35.159 | 37 | 156 |
| turns | 43.1 | 33.0 | 30.2549 | 12 | 103 |
| cells_visited | 42.3 | 39.0 | 26.5153 | 8 | 100 |
| time_seconds | 8.3887 | 8.0121 | 4.5915 | 2.251 | 18.6248 |
| walls_found | 28.15 | 27.0 | 19.6101 | 1 | 63 |
| replan_count | 16.2 | 16.0 | 12.1291 | 1 | 42 |

### Phase3 Metrics
| Metric | Mean | Median | StdDev | Min | Max |
| --- | --- | --- | --- | --- | --- |
| moves | 61.8 | 61.0 | 19.5814 | 29 | 104 |
| turns | 25.7 | 21.0 | 14.758 | 12 | 67 |
| cells_visited | 0 | 0.0 | 0.0 | 0 | 0 |
| time_seconds | 2.5706 | 2.4943 | 0.8676 | 1.2448 | 4.7218 |
| walls_found | 0 | 0.0 | 0.0 | 0 | 0 |
| replan_count | 0 | 0.0 | 0.0 | 0 | 0 |

### Results by Maze Typology
| Typology | Runs | Success | Avg Moves | Avg Time (s) |
| --- | --- | --- | --- | --- |
| competition | 8 | 8/8 | 303.9 | 26.2675 |
| dead_end | 3 | 3/3 | 258.0 | 24.5039 |
| multiple_path | 3 | 3/3 | 339.3 | 32.5773 |
| open_area | 3 | 3/3 | 155.0 | 13.3613 |
| symmetric | 3 | 3/3 | 236.0 | 20.9511 |

### Results by Algorithm Version
| Version | Runs | Success | Avg Moves | Avg Turns | Avg Time (s) | Avg Path Len |
| --- | --- | --- | --- | --- | --- | --- |
| v2 | 20 | 20/20 | 269.8 | 126.6 | 24.2160 | 61.8 |