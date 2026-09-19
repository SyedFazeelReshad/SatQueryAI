"""
SatQuery AI — Instruction Formatting for Remote Sensing VLM
Converts filtered BigEarthNet patch metadata into structured multi-turn Vision-Language instruction dialogues.

Supports:
- Qwen2-VL conversational format
- BLIP-2 / standard causal LM format
- Multi-query diversity (Scene Description, Feature Identification, Land-Cover Breakdown, Counting, Presence Verification)
"""

import random
from typing import Any, Dict, List

# Template variations for Scene Understanding
CAPTION_TEMPLATES = [
    "Describe the land-cover and major environmental features visible in this satellite imagery.",
    "Provide a detailed remote sensing scene description for this patch.",
    "What geographical and anthropogenic features are observed in this image?",
    "Summarize the primary terrain, vegetation, and built-up characteristics of this satellite scene."
]

# Template variations for Specific Feature Verification
PRESENCE_TEMPLATES = [
    ("Is {feature} present in this satellite observation?", "Yes, {feature} is clearly identifiable in this scene.", "No, {feature} is not present in this observation."),
    ("Does this scene contain {feature}?", "Affirmative, the imagery displays {feature}.", "Negative, {feature} is absent from this region."),
    ("Can you detect {feature} in this patch?", "Yes, {feature} was detected.", "No, {feature} was not observed.")
]


def format_qwen2_vl_dialogue(
    image_path: str,
    question: str,
    answer: str
) -> Dict[str, Any]:
    """
    Formats a single QA pair into Qwen2-VL conversational messages structure.
    """
    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": question}
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": answer}
                ]
            }
        ]
    }


def generate_multiturn_conversations(
    patch_id: str,
    image_path: str,
    labels: List[str],
    metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generates diverse conversational training examples for a single remote sensing patch.
    """
    conversations = []
    
    # 1. Main Scene Description / Captioning
    if labels:
        main_question = random.choice(CAPTION_TEMPLATES)
        if len(labels) == 1:
            desc = f"This satellite scene primarily shows {labels[0].lower()}."
        elif len(labels) == 2:
            desc = f"This scene displays a combination of {labels[0].lower()} and {labels[1].lower()}."
        else:
            classes_str = ", ".join([l.lower() for l in labels[:-1]]) + f", and {labels[-1].lower()}"
            desc = f"This remote sensing scene contains multiple land-cover types including {classes_str}."
            
        conversations.append(format_qwen2_vl_dialogue(image_path, main_question, desc))
        
    # 2. Specific Feature Queries (e.g. Water, Forest, Urban)
    target_features = [
        ("water bodies", ["water", "marine", "sea", "lake", "river", "marsh"]),
        ("dense forest", ["forest", "woodland"]),
        ("urban or built-up infrastructure", ["urban", "industrial", "commercial", "road", "rail", "airport"]),
        ("agricultural or cultivated land", ["arable", "crop", "vineyard", "pasture", "orchard"])
    ]
    
    for feat_name, keywords in target_features:
        has_feature = any(any(k in lbl.lower() for k in keywords) for lbl in labels)
        q_template, pos_ans, neg_ans = random.choice(PRESENCE_TEMPLATES)
        
        q = q_template.format(feature=feat_name)
        if has_feature:
            matching = [lbl for lbl in labels if any(k in lbl.lower() for k in keywords)]
            ans = f"{pos_ans.format(feature=feat_name)} Specifically: {', '.join(matching)}."
        else:
            ans = neg_ans.format(feature=feat_name)
            
        conversations.append(format_qwen2_vl_dialogue(image_path, q, ans))
        
    # 3. Grounding / Land-Cover Categorization Query
    cat_q = "List all detected land-cover classifications for this geographic region."
    cat_a = f"Identified classifications: {', '.join(labels)}."
    conversations.append(format_qwen2_vl_dialogue(image_path, cat_q, cat_a))
    
    return conversations
