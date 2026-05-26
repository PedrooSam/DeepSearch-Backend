from rest_framework import serializers


class RiskPredictionInputSerializer(serializers.Serializer):
    activity = serializers.ChoiceField(
        choices=[
            "Surfing", "Swimming", "Wading", "Fishing", "Spearfishing",
            "Bodyboarding", "Unknown", "Snorkeling", "Kayaking", "Scuba Diving",
            "Diving", "Shark Interaction", "Free Diving", "Paddleboarding",
            "Boat / Vessel", "Research / Filming", "Other / Unknown",
        ],
        help_text="Atividade sendo realizada na água."
    )
    time = serializers.CharField(
        required=False, allow_null=True, default=None,
        help_text="Horário do ataque (ex: '14h30', 'Afternoon'). Opcional."
    )
    date = serializers.DateField(
        required=False, allow_null=True, default=None,
        help_text="Data para determinar estação do ano (YYYY-MM-DD). Opcional."
    )
    country = serializers.CharField(
        help_text="País onde ocorre a atividade (ex: 'USA', 'AUSTRALIA', 'BRAZIL')."
    )
    sea_temp = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text="Temperatura do mar em °C. Opcional."
    )
    tide_level = serializers.ChoiceField(
        required=False, allow_null=True, default=None,
        choices=[
            "Alta", "Alta moderada", "Média-alta", "Média enchente",
            "Média-baixa", "Média vazante", "Baixa moderada", "Baixa",
            "Sem influência de maré",
        ],
        help_text="Nível da maré no momento. Opcional."
    )
    clima = serializers.CharField(
        required=False, allow_null=True, default=None,
        help_text=(
            "Descrição do clima (ex: 'Quente, chuva leve, vento moderado, alta umidade'). "
            "Opcional."
        )
    )
    air_temp = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text="Temperatura do ar em °C. Opcional."
    )
    precipitation = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text="Precipitação em mm. Opcional."
    )
    wind_speed = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text="Velocidade máxima do vento em km/h. Opcional."
    )
    lat = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text="Latitude do local. Opcional."
    )
    lon = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text="Longitude do local. Opcional."
    )


class RiskPredictionOutputSerializer(serializers.Serializer):
    probability = serializers.FloatField(help_text="Probabilidade de ataque (0.0 a 1.0).")
    risk_level = serializers.CharField(
        help_text="Nível de risco: 'Muito baixo', 'Baixo', 'Moderado' ou 'Alto'."
    )
