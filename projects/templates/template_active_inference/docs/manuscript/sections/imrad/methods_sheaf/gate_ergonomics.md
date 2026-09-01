The `gate_ergonomics` fragment turns validation commands into evidence rows. `output/data/validation_gate_index.json` records {{validation_gate_index_count}} gate rows, each naming required inputs and the negative-control surface that should fail closed.

`output/data/track_lane_matrix.json` is the cross-track audit table for the same gate surface: {{track_lane_matrix_row_count}} pipeline rows map to sheaf fragments, producer scripts, primary artifacts, validation gates, and manuscript consumers, with completion flag `{{track_lane_matrix_complete}}`.
