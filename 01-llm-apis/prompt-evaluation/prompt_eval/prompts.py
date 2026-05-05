MEAL_PLAN_PROMPT_TEMPLATE = """
    Generate a one-day meal plan for an athelete that meets their dietary restrictions.

    <athelete_information>
    - Height: {height}
    - Weight: {weight}
    - Goal: {goal}
    - Dietary restrictions: {restrictions}
    </athelete_information>

    Guidelines:
    1. Include accurate daily calorie amount
    2. Show protein, fat, and carb amounts
    3. Specify when to eat each meal
    4. Use only foods that fit restrictions
    5. List all portion sizes in grams
    6. Keep budget-friendly if mentioned

    Here is an example with a sample input and an ideal output:
    <sample_input>
    height: 178 cm
    weight: 68 kg
    goal: Marathon training with high-intensity endurance performance
    restrictions: Vegan, gluten-free
    </sample_input>
    <ideal_output>
    # One-Day Vegan, Gluten-Free Marathon Training Meal Plan

    **Athlete Profile:** 178 cm, 68 kg | Estimated Daily Needs: ~2,800-3,200 calories, 110-136g protein, 420-480g carbs

    ---

    ## **BREAKFAST (7:00 AM)** | 650 cal | 18g protein
    - **Gluten-free oatmeal** (60g) with almond milk
    - **Toppings:** sliced banana, ground flaxseed (2 tbsp), almond butter (2 tbsp), maple syrup
    - **Side:** Fresh berries (blueberries, raspberries)
    - **Drink:** Green tea with lemon

    *Why: Quick-digesting carbs + plant-based protein for morning energy*

    ---

    ## **MID-MORNING SNACK (10:00 AM)** | 280 cal | 12g protein
    - **Smoothie bowl:**
      - Plant-based protein powder (vegan, GF) - 1 scoop
      - Coconut milk (½ cup)
      - Banana, mango
      - Granola (GF certified)
      - Hemp seeds

    *Why: Sustained energy before training*

    ---

    ## **LUNCH (1:00 PM)** | 750 cal | 22g protein
    - **Quinoa power bowl:**
      - Cooked quinoa (¾ cup)
      - Roasted sweet potato (150g)
      - Steamed broccoli & bell peppers
      - Baked tofu (120g)
      - Tahini dressing (2 tbsp)
      - Avocado (½)

    *Why: Complete protein + complex carbs for afternoon training*

    ---

    ## **PRE-WORKOUT SNACK (4:00 PM)** | 320 cal | 8g protein
    - **Rice cakes** (2) with almond butter & banana slices
    - **Dates** (3-4) for quick energy
    - **Water with electrolyte powder**

    *Why: Quick carbs + fat for endurance performance*

    ---

    ## **DINNER (7:00 PM)** | 800 cal | 28g protein
    - **Lentil & vegetable stir-fry:**
      - Red lentils (¾ cup cooked)
      - Mixed vegetables (carrots, snap peas, mushrooms)
      - Garlic, ginger, tamari (GF soy sauce)
    - **Brown rice** (¾ cup)
    - **Pumpkin seeds** (2 tbsp) for omega-3s

    *Why: High-quality plant protein + recovery carbs*

    ---

    ## **EVENING SNACK (9:30 PM)** | 200 cal | 8g protein
    - **Homemade energy balls:**
      - Dates + almonds + vegan protein powder
    - **Herbal tea** (chamomile for recovery)

    *Why: Recovery nutrition + sleep support*

    ---

    ## **DAILY TOTALS**
    - **Calories:** ~3,000
    - **Protein:** 96g (12.8% of intake)
    - **Carbs:** 420g (56% of intake)
    - **Fat:** 70g (21% of intake)
    - **Fiber:** 45g+

    ---

    ## **HYDRATION**
    - **Morning-afternoon:** 2-3L water + 1 electrolyte drink during/after training
    - **Evening:** Herbal tea as tolerated

    ---

    ## **NOTES FOR MARATHON TRAINING**
    ✓ Prioritize carb-loading 2-3 days before long runs
    ✓ Adjust portions based on training intensity
    ✓ Consider vegan BCAAs or complete amino acid supplements
    ✓ All items certified gluten-free to avoid cross-contamination
    ✓ Test all foods during training before race day
    </ideal_output>

    <explanation>
    The solution fully satisfies all mandatory requirements with precise daily totals, complete macronutrient breakdowns, and detailed meal timing with exact portions.
    All foods are confirmed vegan and gluten-free. The plan is well-structured for marathon training with appropriate calorie distribution and carbohydrate emphasis.
    Secondary criteria are largely met: meals cover all day periods, are reasonably practical (though some require prep), and provide adequate nutrition.
    The minor protein shortfall relative to elite athlete standards and some preparation complexity prevent a perfect score, but these are minor issues in an otherwise comprehensive solution.
    </explanation>
    """

GRADE_OUTPUT_EXTRA_CRITERIA_TEMPLATE = """
Mandatory Requirements - ANY VIOLATION MEANS AUTOMATIC FAILURE (score of 3 or lower):
<extra_important_criteria>
{extra_criteria}
</extra_important_criteria>
"""

GRADE_OUTPUT_TEMPLATE = """
Your task is to evaluate the following AI-generated solution with EXTREME RIGOR.

Original task description:
<task_description>
{task_description}
</task_description>

Original task inputs:
<task_inputs>
{{ {prompt_inputs} }}
</task_inputs>

Solution to Evaluate:
<solution>
{output}
</solution>

Criteria you should use to evaluate the solution:
<criteria>
{solution_criteria}
</criteria>

{extra_criteria_section}

Scoring Guidelines:
* Score 1-3: Solution fails to meet one or more MANDATORY requirements
* Score 4-6: Solution meets all mandatory requirements but has significant deficiencies in secondary criteria
* Score 7-8: Solution meets all mandatory requirements and most secondary criteria, with minor issues
* Score 9-10: Solution meets all mandatory and secondary criteria

IMPORTANT SCORING INSTRUCTIONS:
* Grade the output based ONLY on the listed criteria. Do not add your own extra requirements.
* If a solution meets all of the mandatory and secondary criteria give it a 10
* Don't complain that the solution "only" meets the mandatory and secondary criteria. Solutions shouldn't go above and beyond - they should meet the exact listed criteria.
* ANY violation of a mandatory requirement MUST result in a score of 3 or lower
* The full 1-10 scale should be utilized - don't hesitate to give low scores when warranted

Output Format
Provide your evaluation as a structured JSON object with the following fields, in this specific order:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement
- "reasoning": A concise explanation of your overall assessment
- "score": A number between 1-10

Respond with JSON. Keep your response concise and direct.
Example response shape:
{{
    "strengths": string[],
    "weaknesses": string[],
    "reasoning": string,
    "score": number
}}
"""

GENERATE_IDEAS_SYSTEM_PROMPT = "You are a test scenario designer specialized in creating diverse, unique testing scenarios."

GENERATE_IDEAS_TEMPLATE = """
Generate {num_cases} unique, diverse ideas for testing a prompt that accomplishes this task:

<task_description>
{task_description}
</task_description>

The prompt will receive the following inputs
<prompt_inputs>
{prompt_inputs_spec}
</prompt_inputs>

Each idea should represent a distinct scenario or example that tests different aspects of the task.

Output Format:
Provide your response as a structured JSON array where each item is a brief description of the idea.

Example:
```json
[
    "Testing with technical computer science terminology",
    "Testing with medical research findings",
    "Testing with complex mathematical concepts",
    ...
]
```

Ensure each idea is:
- Clearly distinct from the others
- Relevant to the task description
- Specific enough to guide generation of a full test case
- Quick to solve without requiring extensive computation or multi-step processing
- Solvable with no more than 400 tokens of output

Remember, only generate {num_cases} unique ideas
"""

GENERATE_TEST_CASE_SYSTEM_PROMPT = (
    "You are a test case creator specializing in designing evaluation scenarios."
)

GENERATE_TEST_CASE_TEMPLATE = """
Generate a single detailed test case for a prompt evaluation based on:

<task_description>
{task_description}
</task_description>

<specific_idea>
{idea}
</specific_idea>

<allowed_input_keys>
{allowed_keys}
</allowed_input_keys>

Output Format:
```json
{{
    "prompt_inputs": {{
    {example_prompt_inputs}
    }},
    "solution_criteria": ["criterion 1", "criterion 2", ...] // Concise list of criteria for evaluating the solution, 1 to 4 items
}}
```

IMPORTANT REQUIREMENTS:
- You MUST ONLY use these exact input keys in your prompt_inputs: {allowed_keys}
- Do NOT add any additional keys to prompt_inputs
- All keys listed in allowed_input_keys must be included in your response
- Make the test case realistic and practically useful
- Include measurable, concise solution criteria
- The solution criteria should ONLY address the direct requirements of the task description and the generated prompt_inputs
- Avoid over-specifying criteria with requirements that go beyond the core task
- Keep solution criteria simple, focused, and directly tied to the fundamental task
- The test case should be tailored to the specific idea provided
- Quick to solve without requiring extensive computation or multi-step processing
- Solvable with no more than 400 tokens of output
- DO NOT include any fields beyond those specified in the output format

Here's an example of a sample input with an ideal output:
<sample_input>
<sample_task_description>
Extract topics out of a passage of text
</sample_task_description>
<sample_specific_idea>
Testing with a text that contains multiple nested topics and subtopics (e.g., a passage about renewable energy that covers solar power economics, wind turbine technology, and policy implications simultaneously)
</sample_specific_idea>

<sample_allowed_input_keys>
"content"
</sample_allowed_input_keys>
</sample_input>
<ideal_output>
```json
{
    "prompt_inputs": {
        "content": "The transition to renewable energy encompasses numerous interdependent dimensions. Solar photovoltaic technology has seen dramatic cost reductions, with panel efficiency improving 24% since 2010 while manufacturing costs declined by 89%, making it economically competitive with fossil fuels in many markets. Concurrently, wind energy has evolved through innovative turbine designs featuring carbon-fiber composite blades and advanced control systems that increase energy capture by 35% in low-wind conditions."
    },
    "solution_criteria": [
        "Includes all topics mentioned"
    ]
}
```
</ideal_output>
This is ideal output because the solution criteria is concise and doesn't ask for anything outside of the scope of the task description.
"""
