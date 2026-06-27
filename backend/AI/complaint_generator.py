from PIL import Image
import os


def _map_severity(confidence):
    if confidence >= 0.85:
        return "Severe"
    if confidence >= 0.60:
        return "Moderate"
    return "Minor"


def _map_priority(confidence):
    if confidence >= 0.90:
        return "Urgent"
    if confidence >= 0.70:
        return "High"
    if confidence >= 0.45:
        return "Medium"
    return "Low"


def _map_department(detected_class):
    mapping = {
        "pothole": "Public Works",
        "garbage": "Sanitation",
        "streetlight": "Electrical",
        "water leak": "Water Services",
        "illegal dumping": "Environmental Services",
    }
    return mapping.get(detected_class.lower(), "Public Works")


def _map_action(detected_class):
    actions = {
        "pothole": "Inspect the road surface, schedule pothole repair, and monitor traffic safety.",
        "garbage": "Dispatch sanitation crew to remove waste and perform area cleanup.",
        "streetlight": "Send an electrical team to inspect and repair the lighting fixture.",
        "water leak": "Open a service ticket for the water department to locate and fix the leak.",
        "illegal dumping": "Arrange removal of debris and increase surveillance in the area.",
    }
    return actions.get(detected_class.lower(), "Inspect the reported issue and escalate to the appropriate department.")


def _map_description(detected_class, confidence):
    if detected_class.lower() == "pothole":
        return (
            "A deep pothole has been detected in the roadway, creating a hazard for vehicles and pedestrians. "
            "The damage appears significant enough to cause vehicle damage if left unattended."
        )
    if detected_class.lower() == "garbage":
        return (
            "A pile of garbage has accumulated in a public area, presenting a health and sanitation issue. "
            "This condition also attracts pests and creates an unpleasant environment for residents."
        )
    if detected_class.lower() == "streetlight":
        return (
            "A streetlight appears to be malfunctioning or out, reducing visibility in the area at night. "
            "This may increase safety risks for pedestrians and drivers after dark."
        )
    return (
        "A civic issue has been identified that requires prompt review and response. "
        "The responsible department should investigate and take corrective action."
    )


def generate_complaint(image_path, detected_class, confidence):
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with Image.open(image_path) as image:
        image.verify()

    severity = _map_severity(confidence)
    priority = _map_priority(confidence)
    department = _map_department(detected_class)
    action = _map_action(detected_class)
    description = _map_description(detected_class, confidence)

    return (
        f"Issue Type: {detected_class.title()}\n"
        f"Severity: {severity}\n"
        f"Description: {description}\n"
        f"Recommended Action: {action}\n"
        f"Department: {department}\n"
        f"Priority: {priority}\n"
        f"Image File: {os.path.basename(image_path)}\n"
        f"Confidence: {confidence:.0%}\n"
    )

if __name__ == "__main__":
    result = generate_complaint(
        image_path="AI/test.jpg",
        detected_class="pothole",
        confidence=0.87
    )
    print("="*50)
    print("COMPLAINT REPORT")
    print("="*50)
    print(result)