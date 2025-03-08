from django import forms
from .models import Prediction

class PredictionForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ['predicted_winner', 'predicted_score']
        widgets = {
            'predicted_winner': forms.Select(choices=[]),
            'predicted_score': forms.TextInput(attrs={'placeholder': '例如: 2-1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.match:
            match = self.instance.match
            self.fields['predicted_winner'] = forms.ChoiceField(
                choices=[(match.team_a, match.team_a), (match.team_b, match.team_b)],
                label='预测获胜队伍'
            )
            
    def clean_predicted_score(self):
        """验证比分格式"""
        score = self.cleaned_data.get('predicted_score')
        if score and not self._is_valid_score_format(score):
            raise forms.ValidationError("比分格式不正确，请使用类似 '3-0' 的格式")
        return score
        
    def _is_valid_score_format(self, score):
        """检查比分格式是否正确"""
        import re
        return bool(re.match(r'^\d+-\d+$', score)) 