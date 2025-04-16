from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FormDoc(BaseModel):
    timestamp: str = Field(description="Carimbo de data/hora da coleta")
    form_number: str = Field(description="Número do Formulário", default=None)
    participant_name: str = Field(description="Nome do participante")
    contact_number: str = Field(description="Número para Contato", default=None)
    location: str = Field(description="Local da coleta")
    age: int = Field(description="Idade do participante em anos")
    sex: str = Field(description="Sexo do participante (Masculino/Feminino)")
    weight: float = Field(description="Peso em kg", default=None)
    height: float = Field(description="Altura em metros ou cm", default=None)
    bmi: float = Field(description="IMC (Índice de Massa Corporal)", default=None)
    race_ethnicity: str = Field(description="Raça ou Etnia autorreferida", default=None)
    smoker: bool = Field(description="Tabagista (Sim/Não)")
    regular_physical_activity: bool = Field(description="Atividade Física Regular (Sim/Não)")
    knowledge_of_ckd_risk_factors: bool = Field(description="Conhecimento sobre fatores de risco para DRC", default=None)
    comorbidities: str = Field(description="Comorbidades (ex: HAS, DM, Obesidade)", default=None)
    other_comorbidities: str = Field(description="Se outras comorbidades, Quais?", default=None)
    creatinine_rapid_test: float = Field(description="Valor de Creatinina Teste Rápido", default=None)
    egfr_rapid_test: float = Field(description="TFGe (Taxa de Filtração Glomerular estimada) em ml/min do teste rápido", default=None)
    ckd_diagnosis_rapid: bool = Field(description="Diagnóstico DRC (TFGe<60 ml/min) do teste rápido", default=None)
    ckd_staging_rapid: str = Field(description="Se DRC, Estadiamento (Sem níveis de Albuminúria) do teste rápido", default=None)
    referral: str = Field(description="Referenciamento", default=None)
    lab_creatinine: float = Field(description="Resultado de laboratório: Creatinina", default=None)
    lab_egfr: float = Field(description="Resultado de Laboratório: TFG", default=None)
    ckd_staging_lab: str = Field(description="Se DRC, Estadiamento pelo resultado do Laboratório (Sem níveis de Albuminúria)", default=None)
