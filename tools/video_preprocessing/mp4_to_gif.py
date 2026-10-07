import argparse
import os
import subprocess

def convert_mp4_to_gif(videopath, outpath, fps=12, scale=None):
    """
    Convert mp4 to gif using ffmpeg.
    fps:   lower fps = smaller file
    scale: e.g. 480, 360, 240 (keeps aspect ratio)
    """
    if not os.path.exists(videopath):
        raise FileNotFoundError(f"Video not found: {videopath}")

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", videopath]

    # Add FPS
    cmd += ["-vf", f"fps={fps}"]

    # Add scaling if provided
    if scale is not None:
        cmd[-1] += f",scale={scale}:-1:flags=lanczos"

    cmd += [outpath]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"GIF saved to: {outpath}")


def main():
    parser = argparse.ArgumentParser(description="Convert .mp4 to .gif")

    parser.add_argument("--videopath", required=True, help="Input .mp4 file")
    parser.add_argument("--outpath", required=True, help="Output .gif file")
    parser.add_argument("--fps", type=int, default=15, help="Output GIF FPS")
    parser.add_argument("--scale", type=int, default=None,
                        help="Width of GIF (height auto). Example: 480")

    args = parser.parse_args()

    convert_mp4_to_gif(args.videopath, args.outpath, args.fps, args.scale)


if __name__ == "__main__":
    main()
# python mp4_to_gif.py --videopath="/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MoveOptical_TAG/EX1/EX1-S12/EX1-S12-face-Full turn_flow.mp4" --outpath="/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MoveOptical_TAG/EX1/EX1-S12/EX1-S12-face-Full turn_flow.gif"
# python mp4_to_gif.py --videopath="/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_TAG/EX1/EX1-S12/EX1-S12-face-Full turn.mp4" --outpath="/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_TAG/EX1/EX1-S12/EX1-S12-face-Full turn.gif"
# python mp4_to_gif.py --videopath="/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MoveSkeleton_TAG/EX1/EX1-S12/EX1-S12-face-Full turn.mp4" --outpath="/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MoveSkeleton_TAG/EX1/EX1-S12/EX1-S12-face-Full turn.gif"

