"""
Voice Authentication Example for Kypzer AI
Simple implementation using Resemblyzer

Author: Kypzer Team
Date: 2026-06-09
"""

from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
from pathlib import Path
import json
import time

class SimpleVoiceAuth:
    """
    Simple voice authentication system
    Train once with your voice, verify every time
    """
    
    def __init__(self, profile_dir=".kiro/voice/"):
        self.encoder = VoiceEncoder()
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = 0.70  # 70% similarity needed
        
    def train(self, audio_files):
        """
        Train on your voice
        
        Args:
            audio_files: List of 5-10 wav files of your voice
        
        Example:
            auth = SimpleVoiceAuth()
            auth.train([
                "my_voice_1.wav",
                "my_voice_2.wav",
                "my_voice_3.wav",
                "my_voice_4.wav",
                "my_voice_5.wav"
            ])
        """
        print("🎤 Training voice profile...")
        print(f"📁 Using {len(audio_files)} voice samples")
        
        embeddings = []
        
        for i, audio_file in enumerate(audio_files, 1):
            print(f"  Processing {i}/{len(audio_files)}: {audio_file}")
            
            try:
                wav = preprocess_wav(audio_file)
                embedding = self.encoder.embed_utterance(wav)
                embeddings.append(embedding)
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
                continue
        
        if not embeddings:
            print("❌ No valid audio files!")
            return False
        
        # Average all embeddings
        profile = np.mean(embeddings, axis=0)
        
        # Save
        profile_path = self.profile_dir / "owner_profile.npy"
        np.save(profile_path, profile)
        
        # Save metadata
        metadata = {
            "trained_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_samples": len(embeddings),
            "threshold": self.threshold
        }
        
        with open(self.profile_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Voice profile saved!")
        print(f"📊 Samples used: {len(embeddings)}")
        print(f"🎯 Threshold: {self.threshold:.0%}")
        
        return True
    
    def verify(self, audio_file):
        """
        Verify if audio matches trained voice
        
        Args:
            audio_file: Path to wav file to verify
        
        Returns:
            (is_authorized: bool, confidence: float)
        
        Example:
            auth = SimpleVoiceAuth()
            is_ok, conf = auth.verify("test_audio.wav")
            
            if is_ok:
                print(f"✅ Authorized! ({conf:.0%} match)")
            else:
                print(f"❌ Unauthorized! ({conf:.0%} match)")
        """
        profile_path = self.profile_dir / "owner_profile.npy"
        
        # Check if trained
        if not profile_path.exists():
            print("⚠️ No voice profile found!")
            print("💡 Run train() first with your voice samples")
            return False, 0.0
        
        # Load profile
        trained_profile = np.load(profile_path)
        
        # Get current audio embedding
        try:
            wav = preprocess_wav(audio_file)
            current_embedding = self.encoder.embed_utterance(wav)
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
            return False, 0.0
        
        # Calculate similarity (cosine similarity)
        similarity = np.dot(trained_profile, current_embedding)
        
        # Decision
        is_authorized = similarity >= self.threshold
        
        return is_authorized, float(similarity)
    
    def adjust_threshold(self, new_threshold):
        """
        Adjust verification threshold
        
        Args:
            new_threshold: Value between 0.0 and 1.0
                          Lower = more lenient (may allow others)
                          Higher = more strict (may reject you)
        
        Recommended:
            0.65 - Very lenient (testing)
            0.70 - Normal (recommended)
            0.75 - Strict (high security)
            0.80 - Very strict (may have false rejections)
        """
        self.threshold = max(0.0, min(1.0, new_threshold))
        print(f"🎯 Threshold adjusted to {self.threshold:.0%}")


# ==========================================
# USAGE EXAMPLES
# ==========================================

def example_training():
    """
    Example: Training the voice authentication system
    """
    print("="*60)
    print("EXAMPLE 1: Training Voice Profile")
    print("="*60)
    
    # Create auth system
    auth = SimpleVoiceAuth()
    
    # Your voice recordings (you need to create these first)
    my_voice_samples = [
        "training_samples/voice_1.wav",
        "training_samples/voice_2.wav",
        "training_samples/voice_3.wav",
        "training_samples/voice_4.wav",
        "training_samples/voice_5.wav",
    ]
    
    # Train
    success = auth.train(my_voice_samples)
    
    if success:
        print("\n✅ Training complete!")
        print("💡 Now you can use verify() to check any audio")
    else:
        print("\n❌ Training failed!")
        print("💡 Make sure audio files exist and are valid WAV files")


def example_verification():
    """
    Example: Verifying a voice command
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Voice Verification")
    print("="*60)
    
    auth = SimpleVoiceAuth()
    
    # Test with your voice
    test_audio = "input.wav"  # Current command audio
    
    is_authorized, confidence = auth.verify(test_audio)
    
    print(f"\n📊 Results:")
    print(f"  Match: {confidence:.2%}")
    print(f"  Threshold: {auth.threshold:.0%}")
    print(f"  Decision: {'✅ AUTHORIZED' if is_authorized else '❌ UNAUTHORIZED'}")
    
    if is_authorized:
        print("\n✅ Access granted! Executing command...")
    else:
        print("\n❌ Access denied! Voice not recognized.")


def example_integration_with_kypzer():
    """
    Example: Integration with Kypzer main loop
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Kypzer Integration")
    print("="*60)
    
    # Initialize
    auth = SimpleVoiceAuth()
    
    # Simulated Kypzer main loop
    while True:
        print("\n🎤 Recording audio...")
        
        # This would be your actual mic.record_audio()
        audio_file = "input.wav"
        
        # VOICE AUTHENTICATION
        is_authorized, confidence = auth.verify(audio_file)
        
        if not is_authorized:
            print(f"❌ Unauthorized! (confidence: {confidence:.2%})")
            print("🔒 Command blocked for security")
            # tts.speak("Access denied. Unauthorized voice.")
            continue  # Skip to next iteration
        
        print(f"✅ Authorized! (confidence: {confidence:.2%})")
        
        # Proceed with command execution
        print("🧠 Processing command...")
        # transcript, _ = stt.transcribe_wav_google(audio_file)
        # ... rest of Kypzer logic
        
        break  # Exit for example


def example_threshold_tuning():
    """
    Example: Finding the right threshold
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Threshold Tuning")
    print("="*60)
    
    auth = SimpleVoiceAuth()
    
    # Test different thresholds
    test_audio = "input.wav"
    thresholds = [0.60, 0.65, 0.70, 0.75, 0.80]
    
    print("\n📊 Testing different thresholds:\n")
    
    for threshold in thresholds:
        auth.adjust_threshold(threshold)
        is_auth, conf = auth.verify(test_audio)
        
        result = "✅ PASS" if is_auth else "❌ FAIL"
        print(f"  Threshold {threshold:.0%}: {result} (match: {conf:.2%})")
    
    print("\n💡 Choose threshold where:")
    print("  - Your voice passes (✅)")
    print("  - Other voices fail (❌)")


def example_continuous_learning():
    """
    Example: Improving profile over time
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Continuous Learning")
    print("="*60)
    
    auth = SimpleVoiceAuth()
    
    # After some successful authentications, update profile
    successful_commands = [
        "command_1.wav",
        "command_2.wav",
        "command_3.wav"
    ]
    
    print("📈 Adding new samples to improve accuracy...")
    
    # Load existing profile
    profile_path = auth.profile_dir / "owner_profile.npy"
    if profile_path.exists():
        old_profile = np.load(profile_path)
        
        # Process new samples
        new_embeddings = []
        for audio in successful_commands:
            try:
                wav = preprocess_wav(audio)
                emb = auth.encoder.embed_utterance(wav)
                new_embeddings.append(emb)
            except:
                pass
        
        if new_embeddings:
            new_avg = np.mean(new_embeddings, axis=0)
            
            # Weighted average (90% old, 10% new)
            updated = 0.9 * old_profile + 0.1 * new_avg
            
            np.save(profile_path, updated)
            print("✅ Profile updated with new samples!")
            print("💡 This helps handle voice changes over time")


# ==========================================
# QUICK START SCRIPT
# ==========================================

def quick_start():
    """
    Quick start guide for voice authentication
    """
    print("\n" + "="*70)
    print("🚀 KYPZER VOICE AUTHENTICATION - QUICK START")
    print("="*70)
    
    print("\n📝 Steps to setup:\n")
    
    print("1️⃣  INSTALL DEPENDENCIES:")
    print("   pip install resemblyzer webrtcvad")
    print()
    
    print("2️⃣  RECORD YOUR VOICE (5-10 samples):")
    print("   - Say different things: 'Hello Kypzer', 'Volume up', 'Open Chrome'")
    print("   - Record 3-5 seconds each")
    print("   - Save as: voice_1.wav, voice_2.wav, ... voice_5.wav")
    print()
    
    print("3️⃣  TRAIN THE SYSTEM:")
    print("   auth = SimpleVoiceAuth()")
    print("   auth.train(['voice_1.wav', 'voice_2.wav', ...])") 
    print()
    
    print("4️⃣  TEST VERIFICATION:")
    print("   is_ok, conf = auth.verify('test.wav')")
    print("   print(f'Authorized: {is_ok}, Confidence: {conf:.0%}')")
    print()
    
    print("5️⃣  INTEGRATE WITH KYPZER:")
    print("   # In main.py:")
    print("   audio = mic.record_audio()")
    print("   if not auth.verify(audio)[0]:")
    print("       continue  # Block unauthorized")
    print()
    
    print("="*70)
    print("✅ That's it! Your Kypzer is now voice-protected!")
    print("="*70)


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    # Run all examples
    quick_start()
    
    # Uncomment to run specific examples:
    # example_training()
    # example_verification()
    # example_integration_with_kypzer()
    # example_threshold_tuning()
    # example_continuous_learning()
