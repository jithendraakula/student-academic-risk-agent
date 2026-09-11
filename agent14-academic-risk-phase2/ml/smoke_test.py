import json

try:
    from .data_loader import build_student_training_frame, load_processed_data
    from .predictor import predict_all_risks
except ImportError:
    from data_loader import build_student_training_frame, load_processed_data
    from predictor import predict_all_risks


def main() -> None:
    data = load_processed_data()
    student_frame = build_student_training_frame(data)
    student = student_frame.iloc[0].drop(labels=[column for column in student_frame.columns if column.endswith("_target") or column.startswith("historical_")]).to_dict()
    courses = data["course"].loc[data["course"]["student_id"] == student["student_id"]].drop(columns=["course_failed"]).to_dict("records")
    result = predict_all_risks(student, courses)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
