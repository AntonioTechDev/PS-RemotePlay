from inference_sdk import InferenceHTTPClient
import cv2
import json

# create an inference client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="wugpeDqxUuUIyHNgG6jX"
)

# run inference on a local image
results = CLIENT.infer("frame_207.jpg", model_id="fifa-ai-0rale/1")

# Print formatted inference results
print(json.dumps(results, indent=2))

# Load the image to draw detections
image = cv2.imread("frame_405.jpg")
if "predictions" in results:
    for pred in results["predictions"]:
        # Calculate top-left coordinates
        x = int(pred["x"] - pred["width"] / 2)
        y = int(pred["y"] - pred["height"] / 2)
        w = int(pred["width"])
        h = int(pred["height"])
        conf = pred["confidence"]
        label = pred["class"]
        # Filter detections with confidence above 0.5
        if conf > 0.5:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, f"{label} {conf:.2f}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.imwrite("annotated_frame_405.jpg", image)
    print("Annotated image saved as annotated_frame_405.jpg")
else:
    print("No predictions found.")