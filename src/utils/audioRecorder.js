// ─────────────────────────────────────────────
//  utils/audioRecorder.js
//
//  Utility for recording audio from the microphone
//  and playing audio from base64 strings.
// ─────────────────────────────────────────────

/**
 * Start recording audio from the user's microphone
 * @returns {Promise<MediaRecorder>} - The MediaRecorder instance
 */
export async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    // Find a supported MIME type
    const mimeTypes = [
      "audio/webm",
      "audio/webm;codecs=opus",
      "audio/ogg;codecs=opus",
      "audio/mp4",
      "", // Default (browser will choose)
    ];

    let selectedMimeType = "";
    for (const mimeType of mimeTypes) {
      if (mimeType === "" || MediaRecorder.isTypeSupported(mimeType)) {
        selectedMimeType = mimeType;
        break;
      }
    }

    const options = selectedMimeType ? { mimeType: selectedMimeType } : {};
    const mediaRecorder = new MediaRecorder(stream, options);

    return mediaRecorder;
  } catch (err) {
    console.error("Error accessing microphone:", err);
    // Provide more detailed error messages
    if (err.name === "NotAllowedError") {
      throw new Error("Microphone permission denied. Please allow microphone access in your browser settings.");
    } else if (err.name === "NotFoundError") {
      throw new Error("No microphone found. Please check your microphone connection.");
    } else if (err.name === "NotReadableError") {
      throw new Error("Could not access microphone. It may be in use by another application.");
    }
    throw err;
  }
}

/**
 * Stop recording and return the audio blob
 * @param {MediaRecorder} mediaRecorder - The MediaRecorder instance
 * @returns {Promise<Blob>} - The recorded audio as a Blob
 */
export function stopRecording(mediaRecorder) {
  return new Promise((resolve) => {
    const chunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      // Stop all audio tracks to release the microphone
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      
      const blob = new Blob(chunks, { type: "audio/wav" });
      resolve(blob);
    };

    mediaRecorder.stop();
  });
}

/**
 * Convert a Blob to base64 string
 * @param {Blob} blob - The blob to convert
 * @returns {Promise<string>} - The base64 encoded string
 */
export function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      // Extract the base64 part after the comma
      const base64 = reader.result.split(",")[1];
      resolve(base64);
    };
    reader.readAsDataURL(blob);
  });
}

/**
 * Play audio from a base64 encoded string
 * @param {string} base64Audio - The base64 encoded audio string
 */
export function playAudio(base64Audio) {
  try {
    // Convert base64 to binary and create a Blob
    const binaryString = atob(base64Audio);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: "audio/wav" });

    // Create a URL and play it
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play().catch((err) => {
      console.error("Error playing audio:", err);
    });
  } catch (err) {
    console.error("Error decoding audio:", err);
  }
}
