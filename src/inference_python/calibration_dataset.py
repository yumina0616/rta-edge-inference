import cv2
import nncf

from preprocess import preprocess

CALIBRATION_VIDEO = "data/videos/14468440_2160_3840_30fps.mp4"
TARGET_FRAME_COUNT = 300

def _sample_frames(video_path: str, target_count: int) -> list:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"영상을 열 수 없음: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 영상 프레임 수 가져오기
    step = max(1, total // target_count)    # 몇 프레임마다 한 장 뽑을건지?

    frames = []
    frame_id = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_id % step == 0:    # frame_id가 step에 걸릴 때마다 저장(몇 프레임마다 한 장 뽑는가?)
            frames.append(frame)
        frame_id += 1
    cap.release()

    return frames[:target_count]


def build_calibration_dataset() -> nncf.Dataset:
    frames = _sample_frames(CALIBRATION_VIDEO, TARGET_FRAME_COUNT)
    
    def transform_fn(frame):
        tensor, _, _ = preprocess(frame)    # return nchw, scale, pad 중 nchw 만
        return tensor
    
    # calibration 데이터를 NNCF가 사용할 수 있도록 감싸주는 wrapper
    return nncf.Dataset(frames, transform_fn)

if __name__ == "__main__":
    frames = _sample_frames(CALIBRATION_VIDEO, TARGET_FRAME_COUNT)
    print("collected frames:", len(frames))