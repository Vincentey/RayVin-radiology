"""
Clinical Knowledge Base for CT and MRI Findings

This module contains curated clinical recommendations for pathologies
detected by the 3D vision models for CT and MRI scans.

Based on:
- ACR Appropriateness Criteria
- Fleischner Society Guidelines (for pulmonary nodules)
- ACR TI-RADS, LI-RADS guidelines
- RSNA guidelines

DISCLAIMER: These recommendations are for clinical decision support only.
They should be reviewed by qualified healthcare professionals and do not
replace clinical judgment.
"""

from typing import List, Dict

# ============================================================
# CT SCAN CLINICAL RECOMMENDATIONS
# ============================================================

CT_RECOMMENDATIONS: List[Dict] = [
    {
        "id": "ct_normal_001",
        "pathology": "Normal",
        "modality": "CT",
        "content": """
NORMAL CT FINDINGS - Clinical Recommendations

Definition:
No significant abnormality detected on CT imaging. Normal anatomical structures
with appropriate density, size, and configuration.

Clinical Significance:
- Reassuring finding when clinical suspicion is low
- Does not completely exclude pathology (sensitivity limitations)
- Findings should be correlated with clinical presentation

Recommended Actions:
1. Correlate with clinical symptoms and physical examination
2. Review prior imaging if available for comparison
3. Consider alternative diagnoses if symptoms persist
4. Routine follow-up as clinically indicated
5. Document normal findings for future reference

Urgency: Routine
Specialty Referral: Not typically required unless symptoms persist
ICD-10 Codes: Z03.89 (Encounter for observation for other suspected conditions)
        """,
        "urgency": "routine",
        "specialty": "none"
    },
    {
        "id": "ct_mass_001",
        "pathology": "Mass",
        "modality": "CT",
        "content": """
MASS (CT) - Clinical Recommendations

Definition:
A space-occupying lesion >3cm in diameter identified on CT. May represent
neoplastic, infectious, or inflammatory process.

Clinical Significance:
- High likelihood of clinical significance requiring further workup
- Malignancy must be excluded, especially in patients with risk factors
- Location, size, and enhancement pattern guide differential diagnosis

Recommended Actions:
1. URGENT: Characterize the mass - location, size, margins, density, enhancement
2. Review prior imaging for comparison to assess stability or growth
3. Obtain contrast-enhanced CT if not already performed
4. Consider PET-CT for metabolic characterization if malignancy suspected
5. Tissue sampling (biopsy) for histopathological diagnosis
6. Tumor markers as clinically appropriate (CEA, AFP, CA-125, PSA)
7. Multidisciplinary tumor board discussion for treatment planning

Differential Diagnoses:
- Primary malignancy (lung cancer, hepatocellular carcinoma, renal cell carcinoma)
- Metastatic disease
- Benign tumors (hamartoma, hemangioma, adenoma)
- Abscess or infectious collection
- Inflammatory mass (granulomatous disease)

Urgency: Urgent - Expedited workup within 1-2 weeks
Specialty Referral: Oncology, Interventional Radiology, Surgery as appropriate
ICD-10 Codes: R91.8 (Other abnormal findings on diagnostic imaging of lung),
              R93.89 (Abnormal findings on diagnostic imaging of other body structures)
        """,
        "urgency": "urgent",
        "specialty": "oncology"
    },
    {
        "id": "ct_nodule_001",
        "pathology": "Nodule",
        "modality": "CT",
        "content": """
PULMONARY NODULE (CT) - Clinical Recommendations

Definition:
A rounded opacity ≤3cm in diameter, completely surrounded by pulmonary
parenchyma. Management per Fleischner Society Guidelines 2017.

Clinical Significance:
- Common incidental finding (up to 50% of CT scans)
- Most are benign, but malignancy risk increases with size and other factors
- Risk stratification guides follow-up intervals

Recommended Actions (Fleischner Society Guidelines):

SOLID NODULES - Low Risk Patient:
- <6mm: No routine follow-up
- 6-8mm: CT at 6-12 months, then consider CT at 18-24 months
- >8mm: CT at 3 months, PET-CT, or tissue sampling

SOLID NODULES - High Risk Patient:
- <6mm: Optional CT at 12 months
- 6-8mm: CT at 6-12 months, then CT at 18-24 months
- >8mm: CT at 3 months, PET-CT, or tissue sampling

SUBSOLID NODULES (Ground-glass or Part-solid):
- <6mm pure GGN: No routine follow-up
- ≥6mm pure GGN: CT at 6-12 months, then every 2 years for 5 years
- Part-solid: CT at 3-6 months, if persistent annual CT for 5 years

Risk Factors for Malignancy:
- Size >8mm
- Irregular or spiculated margins
- Upper lobe location
- Smoking history
- Prior malignancy
- Family history of lung cancer

Urgency: Semi-urgent to Routine (based on size and risk)
Specialty Referral: Pulmonology for nodules requiring biopsy or surveillance
ICD-10 Codes: R91.1 (Solitary pulmonary nodule)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_consolidation_001",
        "pathology": "Consolidation",
        "modality": "CT",
        "content": """
CONSOLIDATION (CT) - Clinical Recommendations

Definition:
Opacification of airspaces with obscuration of underlying vessels.
Air bronchograms may be present. Represents alveolar filling process.

Clinical Significance:
- Most commonly infectious (bacterial pneumonia)
- Can represent organizing pneumonia, hemorrhage, or malignancy
- Distribution pattern helps narrow differential

Recommended Actions:
1. Assess clinical context - fever, cough, dyspnea, immunocompromised status
2. Obtain complete blood count, inflammatory markers (CRP, procalcitonin)
3. Sputum culture and blood cultures if febrile
4. For community-acquired pneumonia: Initiate empiric antibiotics per guidelines
5. For atypical patterns: Consider bronchoscopy with BAL
6. Follow-up imaging in 6-8 weeks to confirm resolution
7. If persistent: Consider biopsy to exclude organizing pneumonia or malignancy

Patterns to Note:
- Lobar consolidation: Typical bacterial pneumonia
- Multifocal: Atypical pneumonia, aspiration, or metastatic disease
- Peripheral/subpleural: Organizing pneumonia (COP)
- Dependent: Aspiration pneumonia

Urgency: Urgent if symptomatic, Semi-urgent if incidental
Specialty Referral: Pulmonology if atypical or non-resolving
ICD-10 Codes: J18.9 (Pneumonia, unspecified), J84.89 (Other interstitial lung diseases)
        """,
        "urgency": "urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_ggo_001",
        "pathology": "Ground_Glass_Opacity",
        "modality": "CT",
        "content": """
GROUND-GLASS OPACITY (CT) - Clinical Recommendations

Definition:
Hazy increased attenuation of lung parenchyma with preservation of
bronchial and vascular margins. Represents partial filling of airspaces.

Clinical Significance:
- Broad differential diagnosis from benign to malignant
- Acute vs chronic presentation guides workup
- May represent early adenocarcinoma (lepidic pattern)

Recommended Actions:

ACUTE GGO:
1. Consider viral pneumonia (COVID-19, influenza, CMV)
2. Assess for pulmonary edema or hemorrhage
3. Check for drug-induced pneumonitis
4. Infectious workup as appropriate

CHRONIC/PERSISTENT GGO:
1. Follow Fleischner Guidelines for subsolid nodules
2. CT surveillance at 3-6 months initially
3. If persistent ≥6mm: Annual surveillance for 5 years minimum
4. If growing or developing solid component: Biopsy or resection
5. Consider PET-CT (limited sensitivity for pure GGO)

Differential Diagnoses:
- Infection (viral, PCP, atypical bacteria)
- Adenocarcinoma in situ or minimally invasive adenocarcinoma
- Pulmonary edema
- Pulmonary hemorrhage
- Drug toxicity
- Hypersensitivity pneumonitis
- Organizing pneumonia

Urgency: Urgent if acute/symptomatic, Semi-urgent if chronic
Specialty Referral: Pulmonology, Thoracic Surgery for persistent lesions
ICD-10 Codes: R91.8 (Other abnormal findings on diagnostic imaging of lung)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_emphysema_001",
        "pathology": "Emphysema",
        "modality": "CT",
        "content": """
EMPHYSEMA (CT) - Clinical Recommendations

Definition:
Permanent enlargement of airspaces distal to terminal bronchioles with
destruction of alveolar walls. Appears as areas of low attenuation without
visible walls.

Clinical Significance:
- Major component of COPD
- Associated with significant morbidity and mortality
- Smoking is primary cause; consider alpha-1 antitrypsin deficiency in young patients

Types:
- Centrilobular: Upper lobe predominant, smoking-related
- Panlobular: Lower lobe predominant, alpha-1 antitrypsin deficiency
- Paraseptal: Subpleural, associated with spontaneous pneumothorax

Recommended Actions:
1. Smoking cessation counseling - most important intervention
2. Pulmonary function tests (spirometry, DLCO, lung volumes)
3. Screen for alpha-1 antitrypsin deficiency if <50 years or lower lobe predominant
4. Assess for pulmonary hypertension (RV enlargement, PA diameter >29mm)
5. Optimize COPD management (bronchodilators, ICS as indicated)
6. Vaccinations (influenza, pneumococcal)
7. Pulmonary rehabilitation referral
8. Consider lung volume reduction surgery or lung transplant evaluation if severe

Urgency: Semi-urgent to Routine
Specialty Referral: Pulmonology for management optimization
ICD-10 Codes: J43.9 (Emphysema, unspecified), J44.9 (COPD, unspecified)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_fibrosis_001",
        "pathology": "Fibrosis",
        "modality": "CT",
        "content": """
PULMONARY FIBROSIS (CT) - Clinical Recommendations

Definition:
Irreversible scarring of lung tissue characterized by reticulation,
honeycombing, traction bronchiectasis, and architectural distortion.

Clinical Significance:
- Progressive and often irreversible
- Idiopathic pulmonary fibrosis (IPF) has poor prognosis
- Pattern recognition crucial for diagnosis (UIP vs NSIP vs others)

HRCT Patterns:
- UIP pattern: Basal/subpleural honeycombing, traction bronchiectasis
- NSIP pattern: Ground-glass with fine reticulation, subpleural sparing
- Organizing pneumonia: Peripheral consolidations

Recommended Actions:
1. URGENT: Pulmonology referral for ILD evaluation
2. Complete pulmonary function tests including DLCO
3. Serologic workup for connective tissue disease
4. Multidisciplinary discussion (MDD) for diagnosis
5. Consider surgical lung biopsy if diagnosis uncertain
6. Antifibrotic therapy (pirfenidone, nintedanib) for IPF
7. Lung transplant evaluation for progressive disease
8. Supplemental oxygen if hypoxemic
9. Pulmonary rehabilitation

Differential Diagnoses:
- Idiopathic pulmonary fibrosis (IPF)
- Connective tissue disease-related ILD
- Chronic hypersensitivity pneumonitis
- Drug-induced fibrosis
- Radiation fibrosis
- Asbestosis

Urgency: Urgent - Requires prompt ILD evaluation
Specialty Referral: Pulmonology (ILD specialist), Rheumatology
ICD-10 Codes: J84.10 (Pulmonary fibrosis, unspecified), J84.112 (IPF)
        """,
        "urgency": "urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_effusion_001",
        "pathology": "Pleural_Effusion",
        "modality": "CT",
        "content": """
PLEURAL EFFUSION (CT) - Clinical Recommendations

Definition:
Abnormal accumulation of fluid in the pleural space. CT allows assessment
of volume, loculation, and associated findings.

Clinical Significance:
- Can be transudative (CHF, cirrhosis) or exudative (infection, malignancy)
- Size and associated findings guide management
- May cause respiratory compromise if large

CT Characteristics to Assess:
- Volume estimation
- Simple vs complex (septations, loculation)
- Pleural enhancement or thickening
- Associated lung parenchymal disease
- Lymphadenopathy suggesting malignancy

Recommended Actions:
1. Assess clinical context (heart failure, infection, malignancy history)
2. If >1cm on lateral decubitus or CT: Consider thoracentesis
3. Send pleural fluid for: Cell count, protein, LDH, glucose, pH, cytology, cultures
4. Apply Light's criteria to differentiate transudate vs exudate
5. For recurrent malignant effusion: Consider pleurodesis or indwelling catheter
6. For empyema: Chest tube drainage, antibiotics, possible surgical decortication
7. Address underlying cause (diuretics for CHF, etc.)

Urgency: Urgent if large/symptomatic, Semi-urgent if small
Specialty Referral: Pulmonology, Thoracic Surgery for complex effusions
ICD-10 Codes: J90 (Pleural effusion, not elsewhere classified), J91.8 (Pleural effusion in other conditions)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_pneumothorax_001",
        "pathology": "Pneumothorax",
        "modality": "CT",
        "content": """
PNEUMOTHORAX (CT) - Clinical Recommendations

Definition:
Air in the pleural space. CT is highly sensitive and can detect occult
pneumothorax not visible on chest radiograph.

Clinical Significance:
- Can be life-threatening if tension physiology develops
- Size and symptoms guide management
- Recurrence risk significant, especially with underlying lung disease

Classification:
- Small: <2cm apex to cupola distance
- Large: ≥2cm apex to cupola distance
- Tension: Mediastinal shift, hemodynamic compromise (EMERGENCY)

Recommended Actions:

TENSION PNEUMOTHORAX:
- EMERGENCY: Immediate needle decompression followed by chest tube

LARGE PNEUMOTHORAX (≥2cm) or SYMPTOMATIC:
1. Chest tube insertion (14-16 Fr pigtail catheter or surgical tube)
2. Supplemental oxygen to accelerate reabsorption
3. Serial imaging to confirm resolution
4. Consider pleurodesis for recurrent pneumothorax

SMALL PNEUMOTHORAX (<2cm), ASYMPTOMATIC:
1. Observation with supplemental oxygen
2. Repeat imaging in 3-6 hours
3. If stable/improving: Outpatient management with close follow-up
4. Activity restrictions until resolved

Prevention of Recurrence:
- Smoking cessation
- Avoid scuba diving, unpressurized flight until resolved
- Consider surgical pleurodesis after second episode

Urgency: Emergent (tension) to Semi-urgent (small, stable)
Specialty Referral: Thoracic Surgery for recurrent or persistent
ICD-10 Codes: J93.0 (Spontaneous tension pneumothorax), J93.11 (Primary spontaneous pneumothorax)
        """,
        "urgency": "emergent",
        "specialty": "thoracic_surgery"
    },
    {
        "id": "ct_lymphadenopathy_001",
        "pathology": "Lymphadenopathy",
        "modality": "CT",
        "content": """
LYMPHADENOPATHY (CT) - Clinical Recommendations

Definition:
Enlarged lymph nodes (>1cm short axis for most stations, >1.5cm for
subcarinal). May be reactive, infectious, or neoplastic.

Clinical Significance:
- Mediastinal/hilar adenopathy often indicates significant pathology
- Must exclude malignancy (primary or metastatic)
- Pattern of involvement helps narrow differential

CT Characteristics to Assess:
- Size (short axis diameter)
- Number and distribution
- Necrosis or calcification
- Enhancement pattern
- Associated findings (lung mass, hepatosplenomegaly)

Recommended Actions:
1. Correlate with clinical history (malignancy, infection, autoimmune)
2. If suspicious for malignancy: PET-CT for metabolic assessment
3. Tissue sampling for histopathology:
   - EBUS-TBNA for mediastinal/hilar nodes
   - EUS-FNA for posterior mediastinal nodes
   - Mediastinoscopy if EBUS non-diagnostic
4. If infectious etiology suspected: AFB smear/culture, fungal studies
5. Serologic workup if sarcoidosis suspected (ACE level, calcium)
6. For reactive adenopathy: Follow-up imaging in 6-8 weeks

Differential Diagnoses:
- Malignancy (lung cancer, lymphoma, metastatic disease)
- Sarcoidosis
- Tuberculosis or fungal infection
- Reactive/inflammatory

Urgency: Urgent if malignancy suspected
Specialty Referral: Pulmonology, Oncology, or Hematology
ICD-10 Codes: R59.0 (Localized enlarged lymph nodes), R59.1 (Generalized enlarged lymph nodes)
        """,
        "urgency": "urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_atelectasis_001",
        "pathology": "Atelectasis",
        "modality": "CT",
        "content": """
ATELECTASIS (CT) - Clinical Recommendations

Definition:
Partial or complete collapse of lung tissue. CT allows precise localization
and identification of underlying cause.

Clinical Significance:
- Often benign (post-operative, mucus plugging)
- Must exclude endobronchial obstruction (tumor, foreign body)
- Can lead to hypoxemia if extensive

Types:
- Obstructive: Endobronchial lesion (central mass, mucus plug)
- Compressive: External compression (effusion, mass)
- Passive: Loss of contact with chest wall (pneumothorax)
- Adhesive: Surfactant deficiency
- Cicatricial: Scarring/fibrosis

Recommended Actions:
1. Identify pattern and likely etiology
2. For obstructive pattern: 
   - Bronchoscopy to evaluate for endobronchial lesion
   - Exclude lung cancer, especially in smokers
3. For post-operative atelectasis:
   - Chest physiotherapy and incentive spirometry
   - Early mobilization
4. For persistent atelectasis (>6 weeks):
   - Follow-up CT to assess resolution
   - Bronchoscopy if not improving
5. Address underlying cause (drain effusion, treat infection)

Urgency: Semi-urgent (rule out malignancy in high-risk patients)
Specialty Referral: Pulmonology if persistent or suspicious for obstruction
ICD-10 Codes: J98.11 (Atelectasis)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "ct_bronchiectasis_001",
        "pathology": "Bronchiectasis",
        "modality": "CT",
        "content": """
BRONCHIECTASIS (CT) - Clinical Recommendations

Definition:
Irreversible bronchial dilatation with bronchial wall thickening.
Signet ring sign (bronchus larger than adjacent artery) is diagnostic.

Clinical Significance:
- Chronic condition with recurrent infections
- May be focal (post-infectious) or diffuse (systemic disease)
- Distribution pattern suggests etiology

Patterns:
- Upper lobe: Cystic fibrosis, ABPA, post-TB
- Lower lobe: Recurrent aspiration, immunodeficiency
- Central: ABPA
- Diffuse: Primary ciliary dyskinesia, immunodeficiency

Recommended Actions:
1. Determine etiology:
   - Sweat chloride test for cystic fibrosis
   - IgE, Aspergillus-specific IgE/IgG for ABPA
   - Immunoglobulin levels (IgG, IgA, IgM, IgG subclasses)
   - Alpha-1 antitrypsin level
2. Sputum culture including AFB and fungal
3. Pulmonary function tests
4. Airway clearance techniques (chest physiotherapy, oscillating devices)
5. Prompt treatment of exacerbations with antibiotics
6. Consider long-term macrolide therapy for frequent exacerbations
7. Vaccinations (influenza, pneumococcal)
8. Pulmonary rehabilitation

Urgency: Semi-urgent
Specialty Referral: Pulmonology for ongoing management
ICD-10 Codes: J47.9 (Bronchiectasis, uncomplicated)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    }
]


# ============================================================
# MRI CLINICAL RECOMMENDATIONS
# ============================================================

MRI_RECOMMENDATIONS: List[Dict] = [
    {
        "id": "mri_normal_001",
        "pathology": "Normal",
        "modality": "MRI",
        "content": """
NORMAL MRI FINDINGS - Clinical Recommendations

Definition:
No significant abnormality detected on MRI. Normal signal characteristics,
morphology, and enhancement patterns of anatomical structures.

Clinical Significance:
- Reassuring finding when clinical suspicion is low
- High sensitivity of MRI makes normal study more conclusive
- Clinical correlation remains important

Recommended Actions:
1. Correlate with clinical presentation and symptoms
2. Review prior imaging for comparison if available
3. Consider alternative diagnoses if symptoms persist
4. Document normal findings for future reference
5. Routine clinical follow-up as appropriate

Urgency: Routine
Specialty Referral: Not typically required
ICD-10 Codes: Z03.89 (Encounter for observation for other suspected conditions)
        """,
        "urgency": "routine",
        "specialty": "none"
    },
    {
        "id": "mri_mass_001",
        "pathology": "Mass",
        "modality": "MRI",
        "content": """
MASS (MRI) - Clinical Recommendations

Definition:
A space-occupying lesion identified on MRI with distinct margins.
MRI provides superior soft tissue characterization compared to CT.

Clinical Significance:
- MRI signal characteristics help narrow differential
- Enhancement pattern crucial for characterization
- Location determines clinical significance and approach

Key MRI Characteristics:
- T1 signal (high: fat, blood, melanin, protein)
- T2 signal (high: fluid, tumor; low: fibrosis, calcium)
- Enhancement pattern (homogeneous, heterogeneous, ring)
- Diffusion restriction (suggests hypercellularity/malignancy)
- Perfusion characteristics

Recommended Actions:
1. Characterize mass with full MRI protocol (T1, T2, FLAIR, DWI, post-contrast)
2. Compare with prior imaging if available
3. Consider advanced MRI techniques (spectroscopy, perfusion)
4. Tissue sampling for histopathology when appropriate
5. Multidisciplinary discussion for treatment planning
6. Stage disease if malignancy confirmed

Urgency: Urgent - Expedited workup within 1-2 weeks
Specialty Referral: Based on location (Neurosurgery, Oncology, etc.)
ICD-10 Codes: Location-specific codes apply
        """,
        "urgency": "urgent",
        "specialty": "oncology"
    },
    {
        "id": "mri_edema_001",
        "pathology": "Edema",
        "modality": "MRI",
        "content": """
EDEMA (MRI) - Clinical Recommendations

Definition:
Increased water content in tissue appearing as T2/FLAIR hyperintensity.
May be vasogenic (extracellular) or cytotoxic (intracellular).

Clinical Significance:
- Vasogenic edema: Associated with tumors, infection, inflammation
- Cytotoxic edema: Indicates cellular injury (infarction)
- Extent affects clinical presentation and prognosis

MRI Characteristics:
- T2/FLAIR hyperintensity
- Vasogenic: Finger-like extension along white matter tracts
- Cytotoxic: Corresponds to vascular territory
- May have mass effect

Recommended Actions:

BRAIN EDEMA:
1. Identify underlying cause (tumor, infection, infarct)
2. Assess for mass effect and herniation risk
3. If significant: Consider corticosteroids (dexamethasone) for vasogenic edema
4. Monitor closely for neurological deterioration
5. Neurosurgical consultation if herniation risk

SOFT TISSUE/MUSCULOSKELETAL EDEMA:
1. Correlate with clinical findings (trauma, infection, tumor)
2. Consider bone marrow edema pattern
3. Rule out fracture, osteomyelitis, or malignancy

Urgency: Urgent if associated with mass effect
Specialty Referral: Neurology/Neurosurgery for brain; Orthopedics for MSK
ICD-10 Codes: G93.6 (Cerebral edema), R93.89 (Other abnormal findings)
        """,
        "urgency": "urgent",
        "specialty": "neurology"
    },
    {
        "id": "mri_hemorrhage_001",
        "pathology": "Hemorrhage",
        "modality": "MRI",
        "content": """
HEMORRHAGE (MRI) - Clinical Recommendations

Definition:
Presence of blood products detected on MRI. Signal characteristics vary
based on age of hemorrhage.

MRI Signal Evolution of Blood:
- Hyperacute (<24h): Oxyhemoglobin - T1 iso, T2 bright
- Acute (1-3 days): Deoxyhemoglobin - T1 iso, T2 dark
- Early subacute (3-7 days): Intracellular methemoglobin - T1 bright, T2 dark
- Late subacute (7-14 days): Extracellular methemoglobin - T1 bright, T2 bright
- Chronic (>14 days): Hemosiderin - T1 dark, T2 dark (blooming on GRE/SWI)

Clinical Significance:
- Intracranial hemorrhage requires urgent evaluation
- Underlying etiology must be identified (vascular malformation, tumor, coagulopathy)
- Age of hemorrhage helps determine timing of event

Recommended Actions:

INTRACRANIAL HEMORRHAGE:
1. EMERGENT neurosurgical consultation
2. Assess for mass effect and herniation
3. Check coagulation status (PT, PTT, platelet count)
4. Blood pressure management
5. CT/MR angiography to exclude vascular malformation
6. Consider underlying tumor (hemorrhagic metastasis, GBM)
7. Reversal of anticoagulation if applicable

OTHER LOCATIONS:
1. Identify source and cause
2. Assess for active bleeding
3. Manage according to location and severity

Urgency: Emergent (intracranial), Urgent (other locations)
Specialty Referral: Neurosurgery, Interventional Radiology
ICD-10 Codes: I62.9 (Intracranial hemorrhage, unspecified), location-specific codes
        """,
        "urgency": "emergent",
        "specialty": "neurosurgery"
    },
    {
        "id": "mri_infarct_001",
        "pathology": "Infarct",
        "modality": "MRI",
        "content": """
INFARCT (MRI) - Clinical Recommendations

Definition:
Tissue death due to ischemia. MRI with DWI is highly sensitive for acute
infarction. Cytotoxic edema causes restricted diffusion.

MRI Findings by Stage:
- Hyperacute (<6h): DWI bright, ADC dark, T2/FLAIR may be normal
- Acute (6-72h): DWI bright, ADC dark, T2/FLAIR hyperintense
- Subacute (3-14 days): DWI bright, ADC normalizing/bright
- Chronic (>14 days): DWI normal, T2/FLAIR hyperintense, volume loss

Clinical Significance:
- Time-critical diagnosis requiring immediate intervention
- "Time is brain" - every minute counts
- DWI-FLAIR mismatch suggests stroke within 4.5 hours

Recommended Actions:

ACUTE STROKE (within treatment window):
1. EMERGENT stroke team activation
2. Determine time of symptom onset (or last known well)
3. IV tPA if within 4.5 hours and no contraindications
4. Consider mechanical thrombectomy if large vessel occlusion (up to 24h in select patients)
5. CT angiography or MR angiography to assess for occlusion
6. Admit to stroke unit for monitoring

POST-ACUTE MANAGEMENT:
1. Secondary stroke prevention workup:
   - Cardiac monitoring for atrial fibrillation
   - Carotid imaging (duplex or CTA/MRA)
   - Echocardiogram (TTE ± TEE)
   - Lipid panel, HbA1c
2. Antiplatelet therapy (aspirin, clopidogrel, or both)
3. Statin therapy
4. Blood pressure management
5. Rehabilitation evaluation

Urgency: EMERGENT - Time-critical intervention
Specialty Referral: Neurology (stroke team), Interventional Neuroradiology
ICD-10 Codes: I63.9 (Cerebral infarction, unspecified), G45.9 (TIA, unspecified)
        """,
        "urgency": "emergent",
        "specialty": "neurology"
    },
    {
        "id": "mri_enhancement_001",
        "pathology": "Enhancement",
        "modality": "MRI",
        "content": """
ABNORMAL ENHANCEMENT (MRI) - Clinical Recommendations

Definition:
Areas of increased signal on post-contrast T1-weighted images indicating
blood-brain barrier breakdown or increased vascularity.

Clinical Significance:
- In brain: Suggests active pathology (tumor, infection, demyelination)
- Pattern and location guide differential diagnosis
- Must be correlated with other MRI sequences

Enhancement Patterns:
- Solid/homogeneous: Low-grade tumor, meningioma
- Ring-enhancing: High-grade glioma, abscess, metastasis
- Nodular: Metastases, granulomatous disease
- Leptomeningeal: Carcinomatosis, infection, inflammation
- Patchy/incomplete ring: Demyelination (MS)

Recommended Actions:
1. Characterize enhancement pattern and distribution
2. Correlate with DWI (abscess shows restricted diffusion)
3. Correlate with T2/FLAIR for perilesional edema
4. Consider spectroscopy for tumor vs non-neoplastic
5. Lumbar puncture if infection or leptomeningeal disease suspected
6. Tissue sampling for definitive diagnosis when indicated
7. Monitor with serial imaging for treatment response

Differential Diagnoses:
- Primary brain tumor
- Metastatic disease
- Abscess
- Demyelinating disease
- Subacute infarct
- Radiation necrosis

Urgency: Urgent - Requires prompt characterization
Specialty Referral: Neurology, Neurosurgery, Neuro-oncology
ICD-10 Codes: R93.0 (Abnormal findings on diagnostic imaging of skull and head)
        """,
        "urgency": "urgent",
        "specialty": "neurology"
    },
    {
        "id": "mri_cyst_001",
        "pathology": "Cyst",
        "modality": "MRI",
        "content": """
CYST (MRI) - Clinical Recommendations

Definition:
Well-circumscribed fluid-containing lesion. Signal follows fluid (T1 dark,
T2 bright) unless complicated by hemorrhage or protein content.

Clinical Significance:
- Most cysts are benign and require no intervention
- Size, location, and effect on adjacent structures guide management
- Complex cysts require closer attention

MRI Characteristics of Simple Cyst:
- T1 hypointense (dark)
- T2 hyperintense (bright)
- No enhancement
- Well-defined margins
- No internal complexity

Complex Features (require further evaluation):
- Internal enhancement
- Thick walls
- Mural nodules
- Restricted diffusion

Recommended Actions:
1. Characterize as simple vs complex
2. Simple cysts: Usually observation only
3. Complex cysts: Further workup to exclude malignancy
4. If symptomatic due to mass effect: Consider aspiration or surgery
5. Location-specific management:
   - Renal cysts: Apply Bosniak classification
   - Hepatic cysts: Usually benign, observe if symptomatic
   - Ovarian cysts: Apply O-RADS classification
   - Brain cysts: Evaluate for obstructive hydrocephalus

Urgency: Routine for simple cysts, Semi-urgent for complex
Specialty Referral: Based on location and complexity
ICD-10 Codes: Location-specific cyst codes
        """,
        "urgency": "routine",
        "specialty": "varies"
    },
    {
        "id": "mri_inflammation_001",
        "pathology": "Inflammation",
        "modality": "MRI",
        "content": """
INFLAMMATION (MRI) - Clinical Recommendations

Definition:
MRI findings suggestive of inflammatory process - T2 hyperintensity,
enhancement, and/or tissue swelling without discrete mass.

Clinical Significance:
- Broad differential including infection, autoimmune, and granulomatous
- Clinical context crucial for interpretation
- May require tissue sampling for definitive diagnosis

MRI Features:
- T2/STIR hyperintensity
- Post-contrast enhancement
- No discrete mass (distinguishes from tumor)
- Adjacent edema
- May see restricted diffusion (abscess)

Recommended Actions:
1. Correlate with clinical findings (fever, pain, elevated inflammatory markers)
2. Laboratory workup:
   - CBC, CRP, ESR
   - Culture (blood, tissue, fluid as appropriate)
   - Autoimmune serologies if indicated
3. Consider infection workup including TB, fungal
4. For musculoskeletal: Consider MRI-guided biopsy if diagnosis unclear
5. For brain: Lumbar puncture for CSF analysis
6. Empiric treatment may be initiated while awaiting diagnosis
7. Follow-up imaging to assess response to therapy

Differential Diagnoses:
- Infectious (bacterial, viral, fungal, TB)
- Autoimmune/inflammatory
- Post-surgical changes
- Radiation-induced inflammation
- Granulomatous disease (sarcoidosis)

Urgency: Semi-urgent to Urgent based on location and severity
Specialty Referral: Infectious Disease, Rheumatology as appropriate
ICD-10 Codes: Location and etiology-specific codes
        """,
        "urgency": "semi-urgent",
        "specialty": "infectious_disease"
    },
    {
        "id": "mri_atrophy_001",
        "pathology": "Atrophy",
        "modality": "MRI",
        "content": """
ATROPHY (MRI) - Clinical Recommendations

Definition:
Tissue volume loss visible as decreased size and/or increased surrounding
CSF/fluid spaces. In brain, manifests as enlarged ventricles and sulci.

Clinical Significance:
- May be age-appropriate or pathological
- Pattern of atrophy suggests underlying etiology
- Correlate with cognitive assessment

Brain Atrophy Patterns:
- Global: Alzheimer's (later), vascular, alcohol-related
- Hippocampal: Alzheimer's disease (early), mesial temporal sclerosis
- Frontal/temporal: Frontotemporal dementia
- Caudate/putamen: Huntington's disease
- Cerebellar: MSA-C, chronic alcohol, spinocerebellar ataxia
- Asymmetric: Corticobasal degeneration

Recommended Actions:
1. Compare with prior imaging to assess progression
2. Cognitive assessment (MMSE, MoCA, neuropsychological testing)
3. Laboratory workup for reversible causes:
   - TSH (hypothyroidism)
   - Vitamin B12 level
   - Syphilis serology (if risk factors)
   - HIV testing
4. Consider CSF biomarkers for Alzheimer's if indicated
5. Genetic testing for hereditary conditions
6. Optimize vascular risk factors
7. Cognitive rehabilitation and support services
8. Advanced care planning discussions as appropriate

Urgency: Routine to Semi-urgent (depending on clinical presentation)
Specialty Referral: Neurology (Cognitive/Behavioral)
ICD-10 Codes: G31.9 (Degenerative disease of nervous system, unspecified),
              F02.80 (Dementia in other diseases classified elsewhere)
        """,
        "urgency": "semi-urgent",
        "specialty": "neurology"
    }
]


# Combined knowledge base for CT and MRI
CT_MRI_RECOMMENDATIONS = CT_RECOMMENDATIONS + MRI_RECOMMENDATIONS


def get_ct_recommendations() -> List[Dict]:
    """Get all CT clinical recommendations."""
    return CT_RECOMMENDATIONS


def get_mri_recommendations() -> List[Dict]:
    """Get all MRI clinical recommendations."""
    return MRI_RECOMMENDATIONS


def get_all_ct_mri_recommendations() -> List[Dict]:
    """Get all CT and MRI clinical recommendations."""
    return CT_MRI_RECOMMENDATIONS


def get_recommendation_by_pathology(pathology: str, modality: str = None) -> Dict:
    """
    Get clinical recommendation for a specific pathology.
    
    Args:
        pathology: Name of the pathology
        modality: Optional filter by modality ("CT" or "MRI")
    
    Returns:
        Recommendation dict or None if not found
    """
    recommendations = CT_MRI_RECOMMENDATIONS
    
    if modality:
        if modality.upper() == "CT":
            recommendations = CT_RECOMMENDATIONS
        elif modality.upper() in ["MRI", "MR"]:
            recommendations = MRI_RECOMMENDATIONS
    
    for rec in recommendations:
        if rec["pathology"].lower() == pathology.lower().replace("_", " "):
            return rec
        if rec["pathology"].lower().replace("_", " ") == pathology.lower().replace("_", " "):
            return rec
    
    return None



