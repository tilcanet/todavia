# core/serializers.py
from rest_framework import serializers
from .models import UsuarioAnonimo, Mensaje

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioAnonimo
        fields = ['id', 'alias', 'edad', 'zona'] 
        # El 'id' es importante devolverlo para que el celular sepa quién es

class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ['texto', 'es_de_la_ia', 'fecha']
