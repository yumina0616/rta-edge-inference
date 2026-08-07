"""letterbox resize + 정규화 + NCHW 변환"""

import cv2
import numpy as np

INPUT_SIZE = 416

def letterbox(frame: np.ndarray, size: int = INPUT_SIZE) -> tuple[np.ndarray, float, tuple[int, int]]:
    """비율 유지 리사이즈 + 여백 패딩.
    (결과 이미지, 스케일, (pdd_x, pad_y))를 반환.
    """
    h, w = frame.shape[:2]
    scale = min(size/h, size/w)
    new_h, new_w = int(round(h*scale)), int(round(w*scale))

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    padded = np.full((size, size, 3), 114, dtype=np.uint8) #가로세로 416, rgb 3채널의 3차원 배열에 114(회색)을 채워넣음.
    pad_x, pad_y = (size - new_w)//2, (size - new_h)//2
    padded[pad_y : pad_y + new_h , pad_x : pad_x + new_w] = resized

    return padded, scale, (pad_x, pad_y)

def preprocess(frame: np.ndarray) -> tuple[np.ndarray, float, tuple[int, int]]:
    """letterbox -> BGR2RGB 정규화 -> NCHW.
    모델에 바로 넣을 수 있는 텐서 반환"""
    padded, scale, pad = letterbox(frame)

    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    normalized = rgb.astype(np.float32) / 255.0

    chw = normalized.transpose(2,0,1) # HWC -> CHW
    nchw = np.expand_dims(chw, axis=0)

    return nchw, scale, pad

if __name__ == "__main__":
    import sys
    from video_reader import read_frames

    for frame_id, frame in read_frames(sys.argv[1]): # 비디오 경로 받음
        tensor, scale, pad = preprocess(frame)
        print("tensor shape:", tensor.shape)  # (1, 3, 416, 416) 확인
        print("dtype:", tensor.dtype)  # float32
        print("value range:", tensor.min(), tensor.max())  # 0.0 ~ 1.0
        break # 첫 번째 프레임만 확인
    