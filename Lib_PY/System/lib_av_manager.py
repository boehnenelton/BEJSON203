"""
Library:      lib_av_manager.py
Family:       System
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.2.0 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-06-03
Description:  Handler for system-level audio and video asset orchestration.
RELATIONAL_ID: de2626-av-hardened-004
"""

import os
import subprocess
import json
import base64
import logging

class AVManager:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg = ffmpeg_path
        # Define allowed base directories for media
        self.allowed_roots = [
            os.path.expanduser("~"),
            "/storage/emulated/0"
        ]

    def _validate_path(self, path_str: str) -> str:
        """
        SECURITY: Ensures paths do not contain null bytes and 
        are restricted to allowed system directories.
        """
        if "\0" in path_str:
            raise ValueError("SECURITY: Null byte detected in path.")
        
        abs_path = os.path.abspath(path_str)
        
        # Check against allowed roots
        is_allowed = False
        for root in self.allowed_roots:
            if abs_path.startswith(os.path.abspath(root)):
                is_allowed = True
                break
        
        if not is_allowed:
            logging.warning(f"SECURITY: Unauthorized path access attempt: {abs_path}")
            raise PermissionError(f"Path outside allowed directories: {abs_path}")
            
        return abs_path

    def run_command(self, args):
        try:
            # Secure execution: list-based arguments, shell=False
            result = subprocess.run(args, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return False, result.stderr
            return True, result.stdout
        except Exception as e:
            return False, str(e)

    def get_info(self, input_file):
        try:
            input_file = self._validate_path(input_file)
            args = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", input_file]
            success, output = self.run_command(args)
            if success:
                return json.loads(output)
        except Exception as e:
            logging.error(f"[AVManager] Probe failed: {e}")
        return None

    def process_with_preset(self, input_file, output_file, preset):
        try:
            input_file = self._validate_path(input_file)
            self._validate_path(os.path.dirname(os.path.abspath(output_file)))
            
            info = self.get_info(input_file)
            if not info: return False, "Could not probe file."
            
            has_video = any(s.get("codec_type") == "video" for s in info.get("streams", []))
            v_codec = preset.get("v_codec", "libx264")
            a_codec = preset.get("a_codec", "copy")
            crf = preset.get("crf")
            scale = preset.get("scale")
            extra = preset.get("extra", "")
            
            args = [self.ffmpeg, "-y", "-i", input_file]
            
            if has_video:
                args.extend(["-c:v", v_codec])
                if crf: args.extend(["-crf", str(crf)])
                if scale: args.extend(["-vf", f"scale={scale}"])
            
            args.extend(["-c:a", a_codec])
            
            if extra:
                args.extend(extra.split())
                
            args.append(output_file)
            return self.run_command(args)
        except Exception as e:
            return False, str(e)

    def split_file(self, input_file, output_pattern, segment_time=300):
        """Splits file into N-minute segments (default 5m/300s)."""
        try:
            input_file = self._validate_path(input_file)
            self._validate_path(os.path.dirname(os.path.abspath(output_pattern)))
            args = [
                self.ffmpeg, "-y", "-i", input_file,
                "-f", "segment", "-segment_time", str(segment_time),
                "-reset_timestamps", "1", "-c", "copy", output_pattern
            ]
            return self.run_command(args)
        except Exception as e:
            return False, str(e)

    def to_base64(self, input_file):
        """Converts file to a Base64 string."""
        try:
            input_file = self._validate_path(input_file)
            with open(input_file, "rb") as f:
                return True, base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            return False, str(e)

    def create_slideshow(self, image_file, audio_file, output_file, preset):
        """Combines a static image and audio into a space-efficient video."""
        try:
            image_file = self._validate_path(image_file)
            audio_file = self._validate_path(audio_file)
            self._validate_path(os.path.dirname(os.path.abspath(output_file)))
            
            v_codec = preset.get("v_codec", "libx264")
            a_codec = preset.get("a_codec", "aac")
            crf = preset.get("crf", 30)
            scale = preset.get("scale", "854:480") # Default to 480p for space
            
            args = [
                self.ffmpeg, "-y", "-loop", "1", "-i", image_file,
                "-i", audio_file, "-c:v", v_codec, "-crf", str(crf),
                "-vf", f"scale={scale},format=yuv420p", "-c:a", a_codec,
                "-shortest", output_file
            ]
            return self.run_command(args)
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    print("AV Manager Library - v2.2 OFFICIAL [SECURITY HARDENED]")
