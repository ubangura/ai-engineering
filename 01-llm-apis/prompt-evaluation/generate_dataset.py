from prompt_eval.dataset_generator import DatasetGenerator

dataset_generator = DatasetGenerator(max_concurrent_tasks=1)

dataset = dataset_generator.generate_dataset(
    task_description="Write a compact, concise 1 day meal plan for an athlete",
    prompt_inputs_spec={
        "height": "Athlete's height in cm",
        "weight": "Athlete's weight in kg",
        "goal": "Goal of the athlete",
        "restrictions": "Dietary restrictions of the athlete",
    },
    output_file="data/dataset.json",
    num_cases=3,
)
