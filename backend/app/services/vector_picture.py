# from app import schemas
# from openai import OpenAI
# import base64
# import json
# import numpy as np
# from app.core.config import settings

# # OpenAIクライアント
# openai_client = OpenAI(api_key=settings.API_KEY)

# # Function Calling（tool）で画像から特徴抽出
# def call_openai_image_feature_extraction(image_bytes: bytes) -> schemas.SongFeatureBase:
#     prompt = (
#         "この画像に合う音楽を考えるため、以下の観点で画像を評価してください：\n"
#         "tempo\nenergy\ndanceability\nvalence\n"
#         "それぞれに0〜1の数値でスコア（0:低, 1:高）をつけてください。"
#     )

#     base64_image = base64.b64encode(image_bytes).decode()

#     response = openai_client.chat.completions.create(
#         model="gpt-4o",  # ← 最新・最強モデル
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": prompt},
#                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
#                 ]
#             }
#         ],
#         tools=[
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "extract_song_features",
#                     "description": "画像に基づいて楽曲の特徴量（0〜1）を返す",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "tempo": {"type": "number", "minimum": 0.0, "maximum": 1.0},
#                             "energy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
#                             "danceability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
#                             "valence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
#                         },
#                         "required": ["tempo", "energy", "danceability", "valence"]
#                     }
#                 }
#             }
#         ],
#         tool_choice="auto",  # 自動で関数を使わせる
#         temperature=0.4,
#     )

#     arguments_json = response.choices[0].message.tool_calls[0].function.arguments
#     parsed_args = json.loads(arguments_json)

#     return schemas.SongFeatureBase(**parsed_args)

# # 特徴量をベクトルに変換（学習や類似度計算用）
# def feature_to_vector(f: schemas.SongFeatureBase) -> np.ndarray:
#     return np.array([f.tempo, f.energy, f.danceability, f.valence])