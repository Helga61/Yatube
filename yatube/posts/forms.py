from django import forms
from django.forms import Select, Textarea

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        widgets = {
            'text': Textarea(attrs={
                'cols': 40,
                'rows': 10,
                'class': 'form-control',
                "required id": 'id_text',
            }),
            "group": Select(attrs={
                'select name': 'group',
                'class': 'form-control',
                'id': 'id_group'
            })
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={
                'cols': 40,
                'rows': 10,
                'class': 'form-control',
                "required id": 'id_text',
            })
        }
