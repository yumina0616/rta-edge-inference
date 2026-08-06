"""저장 영상을 프레임 단위로 순차 순회하는 제너레이터."""

from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

def read_frames(video_path: str | Path) -> Iterator[tuple[int, np.array]]:
    """영상에서 (frame_id, framd(BGR))을 순서대로 내보냄."""

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise FileNotFoundError(f"영상을 열 수 없음: {video_path}")

    frame_id = 0
    
    try:
        while True:
            ok, frame = cap.read()
            if not ok: break
            yield frame_id, frame
            frame_id += 1

    finally:
        cap.release()


if __name__ == "__main__":
    import sys
    video_path = sys.argv[1]
    for frame_id, frame in read_frames(video_path):
        if frame_id == 0:
            cv2.imwrite("first_frame_preview.png", frame)
            print("shape:", frame.shape) # 결과: (H, W, 3)
            break