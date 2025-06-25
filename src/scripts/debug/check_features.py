import joblib

model = joblib.load(r"C:\Users\lucap\Projects\P1v2\modeling\win_model.pkl")

if hasattr(model, "feature_names_in_"):
    print("Features used by the model:")
    print(list(model.feature_names_in_))
elif hasattr(model, "named_steps"):
    found = False
    for step_name, step in model.named_steps.items():
        if hasattr(step, "feature_names_in_"):
            print(f"Features used by the step '{step_name}':")
            print(list(step.feature_names_in_))
            found = True
    if not found:
        print("No steps with feature_names_in_ found in the pipeline.")
else:
    print(
        "Feature names not found in the model. Check your training script for the feature list."
    )
