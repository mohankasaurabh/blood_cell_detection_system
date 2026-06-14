def count_cells(detections):

    counts = {
        "RBC": 0,
        "WBC": 0,
        "Platelet": 0,
        "Parasite": 0
    }

    confidences = {
        "RBC": [],
        "WBC": [],
        "Platelet": [],
        "Parasite": []
    }

    for detection in detections:

        class_name = detection["class_name"]
        confidence = detection["confidence"]

        if class_name in counts:
            counts[class_name] += 1
            confidences[class_name].append(confidence)

    averages = {}

    for cls_name, values in confidences.items():

        if len(values) == 0:
            averages[cls_name] = 0
        else:
            averages[cls_name] = round(
                sum(values) / len(values) * 100,
                2
            )

    return counts, averages