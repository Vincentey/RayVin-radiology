"""
Clinical Knowledge Base for Chest X-Ray Findings

This module contains curated clinical recommendations for pathologies
detected by the TorchXRayVision model. Recommendations are based on
established medical guidelines including:
- ACR Appropriateness Criteria
- Fleischner Society Guidelines
- AHA/ACC Guidelines
- BTS Guidelines

DISCLAIMER: These recommendations are for clinical decision support only.
They should be reviewed by qualified healthcare professionals and do not
replace clinical judgment.
"""

from typing import List, Dict

# TorchXRayVision pathologies (densenet121-res224-all model)
PATHOLOGY_RECOMMENDATIONS: List[Dict] = [
    {
        "id": "atelectasis_001",
        "pathology": "Atelectasis",
        "content": """
ATELECTASIS - Clinical Recommendations

Definition:
Partial or complete collapse of lung tissue due to obstruction, compression, 
or loss of surfactant. Appears as increased opacity with volume loss on chest radiograph.

Clinical Significance:
- May indicate mucus plugging, endobronchial obstruction, or post-surgical changes
- Can be associated with underlying malignancy if persistent
- May lead to hypoxemia and respiratory compromise if extensive

Recommended Actions:
1. Correlate with clinical history (recent surgery, intubation, immobility)
2. Assess for signs of respiratory distress
3. Consider bronchoscopy if obstruction suspected
4. Chest physiotherapy and incentive spirometry for post-operative cases
5. Follow-up imaging in 4-6 weeks if persistent to exclude underlying lesion

Differential Diagnoses:
- Mucus plugging
- Endobronchial tumor
- Foreign body aspiration
- Post-operative changes
- Pleural effusion with compressive atelectasis

Urgency: Routine to Semi-urgent (depends on extent and symptoms)
Specialty Referral: Pulmonology if persistent or recurrent
ICD-10 Codes: J98.11 (Atelectasis)
        """,
        "urgency": "routine",
        "specialty": "pulmonology"
    },
    {
        "id": "cardiomegaly_001",
        "pathology": "Cardiomegaly",
        "content": """
CARDIOMEGALY - Clinical Recommendations

Definition:
Enlargement of the cardiac silhouette on chest radiograph. Cardiothoracic ratio 
>0.5 on PA view or >0.55 on AP view suggests cardiomegaly.

Clinical Significance:
- May indicate heart failure, cardiomyopathy, valvular disease, or pericardial effusion
- Important marker for cardiovascular morbidity and mortality
- Requires correlation with symptoms and further cardiac evaluation

Recommended Actions:
1. Correlate with clinical symptoms (dyspnea, orthopnea, peripheral edema, fatigue)
2. Order echocardiogram for structural and functional assessment
3. Consider BNP or NT-proBNP levels to assess for heart failure
4. Review prior chest radiographs for comparison and progression
5. ECG to assess for arrhythmias, ischemia, or chamber enlargement
6. Consider cardiac MRI if echocardiogram is inconclusive

Differential Diagnoses:
- Dilated cardiomyopathy
- Hypertensive heart disease
- Valvular heart disease (aortic stenosis, mitral regurgitation)
- Pericardial effusion
- Congenital heart disease
- High-output states (anemia, thyrotoxicosis)

Urgency: Semi-urgent - Cardiology evaluation within 1-2 weeks
Specialty Referral: Cardiology
ICD-10 Codes: I51.7 (Cardiomegaly), I50.9 (Heart failure, unspecified)
        """,
        "urgency": "semi-urgent",
        "specialty": "cardiology"
    },
    {
        "id": "consolidation_001",
        "pathology": "Consolidation",
        "content": """
CONSOLIDATION - Clinical Recommendations

Definition:
Replacement of alveolar air with fluid, cells, or other material. Appears as 
homogeneous opacification with air bronchograms on chest radiograph.

Clinical Significance:
- Most commonly indicates pneumonia (bacterial, viral, fungal)
- May represent pulmonary hemorrhage, aspiration, or malignancy
- Requires prompt evaluation and treatment if infectious

Recommended Actions:
1. Assess vital signs and oxygen saturation immediately
2. Obtain complete blood count, inflammatory markers (CRP, procalcitonin)
3. Collect sputum culture and blood cultures if febrile
4. Start empiric antibiotics per local guidelines if pneumonia suspected
5. Consider CT chest if atypical presentation or poor response to treatment
6. Follow-up chest radiograph in 6-8 weeks to confirm resolution

Differential Diagnoses:
- Community-acquired pneumonia
- Hospital-acquired pneumonia
- Aspiration pneumonia
- Pulmonary hemorrhage
- Cryptogenic organizing pneumonia
- Bronchioloalveolar carcinoma

Urgency: Urgent - Same-day evaluation recommended
Specialty Referral: Pulmonology if complicated or non-resolving
ICD-10 Codes: J18.9 (Pneumonia, unspecified), J69.0 (Aspiration pneumonia)
        """,
        "urgency": "urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "edema_001",
        "pathology": "Edema",
        "content": """
PULMONARY EDEMA - Clinical Recommendations

Definition:
Accumulation of fluid in the pulmonary interstitium and alveoli. Radiographic 
signs include cephalization, Kerley B lines, perihilar haziness, and bilateral 
alveolar opacities.

Clinical Significance:
- Cardiogenic edema suggests left heart failure or volume overload
- Non-cardiogenic edema (ARDS) indicates acute lung injury
- Requires urgent evaluation and management

Recommended Actions:
1. Immediate assessment of respiratory status and oxygen saturation
2. Obtain ECG to assess for ischemia or arrhythmia
3. Check BNP/NT-proBNP to differentiate cardiogenic from non-cardiogenic
4. Echocardiogram to assess cardiac function
5. Diuretic therapy if cardiogenic (furosemide IV)
6. Identify and treat underlying cause
7. Consider ICU admission if severe respiratory distress

Differential Diagnoses:
- Acute decompensated heart failure
- Acute coronary syndrome
- Flash pulmonary edema (renal artery stenosis)
- ARDS (sepsis, aspiration, trauma)
- Fluid overload (renal failure, iatrogenic)
- Negative pressure pulmonary edema

Urgency: Emergent to Urgent - Immediate evaluation required
Specialty Referral: Cardiology and/or Critical Care
ICD-10 Codes: J81.0 (Acute pulmonary edema), I50.1 (Left ventricular failure)
        """,
        "urgency": "emergent",
        "specialty": "cardiology"
    },
    {
        "id": "effusion_001",
        "pathology": "Effusion",
        "content": """
PLEURAL EFFUSION - Clinical Recommendations

Definition:
Abnormal accumulation of fluid in the pleural space. Appears as blunting of 
costophrenic angle, meniscus sign, or complete opacification of hemithorax.

Clinical Significance:
- May be transudative (heart failure, cirrhosis) or exudative (infection, malignancy)
- Large effusions can cause respiratory compromise
- Diagnostic thoracentesis often required to determine etiology

Recommended Actions:
1. Assess respiratory status and need for urgent drainage
2. Lateral decubitus radiograph or ultrasound to confirm and quantify
3. Diagnostic thoracentesis if new, unexplained, or symptomatic
4. Fluid analysis: protein, LDH, cell count, glucose, pH, cytology, cultures
5. Apply Light's criteria to differentiate transudate vs exudate
6. CT chest with contrast if malignancy suspected
7. Therapeutic drainage if large or causing respiratory compromise

Differential Diagnoses:
- Congestive heart failure (most common transudate)
- Parapneumonic effusion / empyema
- Malignant effusion
- Pulmonary embolism
- Tuberculosis
- Cirrhosis with hepatic hydrothorax

Urgency: Semi-urgent to Urgent (depends on size and symptoms)
Specialty Referral: Pulmonology; Interventional Radiology for drainage
ICD-10 Codes: J90 (Pleural effusion), J91.0 (Malignant pleural effusion)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "emphysema_001",
        "pathology": "Emphysema",
        "content": """
EMPHYSEMA - Clinical Recommendations

Definition:
Permanent enlargement of airspaces distal to terminal bronchioles with 
destruction of alveolar walls. Radiographic signs include hyperinflation, 
flattened diaphragms, and increased retrosternal airspace.

Clinical Significance:
- Major component of COPD
- Progressive and irreversible lung destruction
- Associated with smoking and alpha-1 antitrypsin deficiency

Recommended Actions:
1. Assess for smoking history and counsel on cessation
2. Pulmonary function tests (spirometry) if not recently done
3. Consider alpha-1 antitrypsin level in younger patients (<50) or non-smokers
4. Optimize bronchodilator therapy (LAMA, LABA, ICS as indicated)
5. Vaccinations (influenza, pneumococcal, COVID-19)
6. Pulmonary rehabilitation referral
7. Assess for supplemental oxygen needs

Differential Diagnoses:
- COPD (most common)
- Alpha-1 antitrypsin deficiency
- Bullous lung disease
- Lymphangioleiomyomatosis (in women)

Urgency: Routine - Outpatient pulmonology follow-up
Specialty Referral: Pulmonology
ICD-10 Codes: J43.9 (Emphysema, unspecified), J44.9 (COPD, unspecified)
        """,
        "urgency": "routine",
        "specialty": "pulmonology"
    },
    {
        "id": "fibrosis_001",
        "pathology": "Fibrosis",
        "content": """
PULMONARY FIBROSIS - Clinical Recommendations

Definition:
Scarring and thickening of lung tissue with reduced lung compliance. 
Radiographic signs include reticular opacities, honeycombing, traction 
bronchiectasis, and volume loss (typically basal predominant).

Clinical Significance:
- May be idiopathic (IPF) or secondary to known causes
- Progressive disease with significant morbidity and mortality
- Early referral to ILD specialist recommended

Recommended Actions:
1. High-resolution CT chest for detailed characterization
2. Pulmonary function tests including DLCO
3. Detailed occupational and exposure history
4. Serologic workup for connective tissue diseases (ANA, RF, anti-CCP)
5. Consider surgical lung biopsy if diagnosis uncertain
6. Refer to interstitial lung disease specialist
7. Evaluate for antifibrotic therapy (pirfenidone, nintedanib) if IPF

Differential Diagnoses:
- Idiopathic pulmonary fibrosis (IPF)
- Hypersensitivity pneumonitis
- Connective tissue disease-associated ILD
- Asbestosis
- Drug-induced lung disease
- Radiation fibrosis

Urgency: Semi-urgent - ILD specialist evaluation within 2-4 weeks
Specialty Referral: Pulmonology (ILD specialist)
ICD-10 Codes: J84.10 (Pulmonary fibrosis, unspecified), J84.112 (IPF)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "hernia_001",
        "pathology": "Hernia",
        "content": """
HIATAL HERNIA - Clinical Recommendations

Definition:
Herniation of abdominal contents (typically stomach) through the esophageal 
hiatus into the thorax. Appears as retrocardiac mass with air-fluid level.

Clinical Significance:
- Common incidental finding, often asymptomatic
- May cause GERD symptoms, dysphagia, or chest pain
- Large paraesophageal hernias at risk for incarceration

Recommended Actions:
1. Correlate with GI symptoms (heartburn, regurgitation, dysphagia)
2. Consider upper GI series or CT for better characterization
3. Trial of proton pump inhibitor therapy if symptomatic
4. Surgical referral for large paraesophageal hernias or severe symptoms
5. Endoscopy if alarm symptoms (dysphagia, weight loss, anemia)

Differential Diagnoses:
- Sliding hiatal hernia (most common)
- Paraesophageal hernia
- Diaphragmatic eventration
- Morgagni hernia
- Bochdalek hernia (congenital)

Urgency: Routine (unless signs of incarceration - then emergent)
Specialty Referral: Gastroenterology; General Surgery if large
ICD-10 Codes: K44.9 (Diaphragmatic hernia without obstruction)
        """,
        "urgency": "routine",
        "specialty": "gastroenterology"
    },
    {
        "id": "infiltration_001",
        "pathology": "Infiltration",
        "content": """
PULMONARY INFILTRATE - Clinical Recommendations

Definition:
Abnormal substance or cells within the lung parenchyma causing increased 
opacity. Non-specific term encompassing various pathologies.

Clinical Significance:
- Broad differential including infection, inflammation, and malignancy
- Clinical context essential for appropriate management
- May require further imaging or tissue sampling for diagnosis

Recommended Actions:
1. Correlate with clinical presentation (fever, cough, dyspnea)
2. Review prior imaging for comparison
3. Laboratory workup: CBC, inflammatory markers, cultures
4. Consider CT chest for better characterization
5. Bronchoscopy with BAL if diagnosis unclear
6. Follow-up imaging to assess resolution or progression

Differential Diagnoses:
- Pneumonia (bacterial, viral, fungal)
- Pulmonary hemorrhage
- Aspiration
- Eosinophilic pneumonia
- Drug reaction
- Malignancy (primary or metastatic)

Urgency: Varies based on clinical presentation
Specialty Referral: Pulmonology if unclear etiology
ICD-10 Codes: R91.8 (Other nonspecific abnormal finding of lung)
        """,
        "urgency": "semi-urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "mass_001",
        "pathology": "Mass",
        "content": """
PULMONARY MASS - Clinical Recommendations

Definition:
Lesion >3 cm in diameter within the lung parenchyma. High suspicion for 
malignancy until proven otherwise.

Clinical Significance:
- Primary lung cancer most common cause in adults
- Requires urgent evaluation and tissue diagnosis
- Staging workup needed if malignancy confirmed

Recommended Actions:
1. URGENT: CT chest with contrast for characterization
2. Review prior imaging - new vs stable
3. PET-CT for metabolic activity and staging
4. Tissue diagnosis: CT-guided biopsy, bronchoscopy, or surgical
5. Multidisciplinary tumor board discussion
6. Complete staging workup if malignancy confirmed
7. Smoking cessation counseling

Differential Diagnoses:
- Primary lung cancer (non-small cell, small cell)
- Metastatic disease
- Lymphoma
- Hamartoma (benign)
- Granulomatous infection (TB, fungal)
- Lung abscess

Urgency: URGENT - Expedited workup within 1-2 weeks
Specialty Referral: Pulmonology, Oncology, Thoracic Surgery
ICD-10 Codes: R91.1 (Solitary pulmonary nodule), C34.90 (Lung cancer)
        """,
        "urgency": "urgent",
        "specialty": "oncology"
    },
    {
        "id": "nodule_001",
        "pathology": "Nodule",
        "content": """
PULMONARY NODULE - Clinical Recommendations

Definition:
Rounded opacity ≤3 cm in diameter within the lung. Management depends on 
size, characteristics, and patient risk factors per Fleischner Society guidelines.

Clinical Significance:
- Most small nodules are benign (granulomas, lymph nodes)
- Risk of malignancy increases with size, spiculation, and growth
- Follow Fleischner guidelines for surveillance

Recommended Actions (per Fleischner Society 2017):
For solid nodules in high-risk patients:
- <6 mm: Optional CT at 12 months
- 6-8 mm: CT at 6-12 months, then 18-24 months
- >8 mm: CT at 3 months, PET/CT, or tissue sampling

For solid nodules in low-risk patients:
- <6 mm: No routine follow-up
- 6-8 mm: CT at 6-12 months
- >8 mm: CT at 3 months, PET/CT, or tissue sampling

Additional Recommendations:
1. Assess patient risk factors (smoking, family history, exposures)
2. Review prior imaging for comparison
3. Consider lung cancer screening for eligible patients
4. Document nodule in radiology follow-up system

Urgency: Routine to Semi-urgent (based on size and characteristics)
Specialty Referral: Pulmonology for nodules >8mm or growing
ICD-10 Codes: R91.1 (Solitary pulmonary nodule)
        """,
        "urgency": "routine",
        "specialty": "pulmonology"
    },
    {
        "id": "pleural_thickening_001",
        "pathology": "Pleural_Thickening",
        "content": """
PLEURAL THICKENING - Clinical Recommendations

Definition:
Abnormal thickening of the pleural lining. May be focal or diffuse, 
unilateral or bilateral.

Clinical Significance:
- Often sequel of prior infection, trauma, or asbestos exposure
- Diffuse pleural thickening may cause restrictive lung disease
- Must exclude malignant mesothelioma in appropriate clinical context

Recommended Actions:
1. Obtain detailed occupational history (asbestos exposure)
2. Review prior imaging for progression
3. CT chest for detailed characterization
4. Pulmonary function tests to assess restriction
5. Consider pleural biopsy if new, progressive, or nodular
6. Regular surveillance if asbestos-related

Differential Diagnoses:
- Prior infection (empyema, TB)
- Asbestos-related pleural disease
- Prior hemothorax or trauma
- Malignant mesothelioma
- Metastatic pleural disease
- Fibrothorax

Urgency: Routine (unless suspicious features - then semi-urgent)
Specialty Referral: Pulmonology; Occupational Medicine if asbestos exposure
ICD-10 Codes: J92.9 (Pleural plaque without asbestos), J92.0 (with asbestos)
        """,
        "urgency": "routine",
        "specialty": "pulmonology"
    },
    {
        "id": "pneumonia_001",
        "pathology": "Pneumonia",
        "content": """
PNEUMONIA - Clinical Recommendations

Definition:
Infection of the lung parenchyma causing inflammation and consolidation. 
Radiographic findings include airspace opacity, air bronchograms, and 
possible pleural effusion.

Clinical Significance:
- Leading cause of infectious death worldwide
- Requires prompt antibiotic therapy
- Severity assessment guides treatment setting (outpatient vs hospital)

Recommended Actions:
1. Assess severity using CURB-65 or PSI score
2. Obtain vital signs including oxygen saturation
3. Laboratory: CBC, BMP, inflammatory markers, procalcitonin
4. Blood cultures (2 sets) before antibiotics if hospitalized
5. Sputum culture and Gram stain if productive cough
6. Start empiric antibiotics per local guidelines:
   - Outpatient: Amoxicillin or doxycycline (low risk)
   - Inpatient: Beta-lactam + macrolide or respiratory fluoroquinolone
7. Consider urinary antigens (Legionella, pneumococcus) if severe
8. Follow-up chest radiograph in 6-8 weeks to confirm resolution

CURB-65 Criteria (1 point each):
- Confusion
- Urea >7 mmol/L
- Respiratory rate ≥30
- Blood pressure (SBP <90 or DBP ≤60)
- Age ≥65

Urgency: Urgent - Same-day evaluation and treatment
Specialty Referral: Pulmonology if complicated or non-resolving
ICD-10 Codes: J18.9 (Pneumonia, unspecified), J15.9 (Bacterial)
        """,
        "urgency": "urgent",
        "specialty": "pulmonology"
    },
    {
        "id": "pneumothorax_001",
        "pathology": "Pneumothorax",
        "content": """
PNEUMOTHORAX - Clinical Recommendations

Definition:
Air in the pleural space causing lung collapse. Appears as visible visceral 
pleural line with absent lung markings peripherally.

Clinical Significance:
- May be spontaneous (primary or secondary) or traumatic
- Tension pneumothorax is a medical emergency
- Size and symptoms determine management

Recommended Actions:

TENSION PNEUMOTHORAX (hypotension, tracheal deviation):
- IMMEDIATE needle decompression (2nd intercostal space, midclavicular)
- Followed by chest tube insertion
- Do NOT wait for imaging if clinically suspected

SIMPLE PNEUMOTHORAX:
Small (<2 cm at hilum) and asymptomatic:
1. Observation with repeat CXR in 6 hours
2. High-flow oxygen (accelerates resorption)
3. Outpatient follow-up if stable

Large (>2 cm) or symptomatic:
1. Chest tube or pigtail catheter insertion
2. Connect to underwater seal or Heimlich valve
3. Repeat CXR to confirm lung re-expansion
4. Thoracic surgery referral if persistent air leak

Recurrent pneumothorax:
- Consider pleurodesis or surgical intervention (VATS)

Urgency: Emergent (tension) to Urgent (simple)
Specialty Referral: Thoracic Surgery for recurrent or persistent
ICD-10 Codes: J93.0 (Spontaneous tension), J93.11 (Primary spontaneous)
        """,
        "urgency": "emergent",
        "specialty": "thoracic_surgery"
    },
    {
        "id": "enlarged_cardiomediastinum_001",
        "pathology": "Enlarged Cardiomediastinum",
        "content": """
ENLARGED CARDIOMEDIASTINUM - Clinical Recommendations

Definition:
Widening of the mediastinal silhouette on chest radiograph. May indicate 
cardiac enlargement, vascular abnormality, or mediastinal mass.

Clinical Significance:
- Wide differential diagnosis requiring correlation with clinical context
- Acute widening may indicate aortic pathology (dissection, aneurysm)
- Chronic widening often due to cardiac or vascular causes

Recommended Actions:
1. Compare with prior imaging if available
2. Assess for acute symptoms (chest pain, hypotension)
3. If acute aortic syndrome suspected:
   - STAT CT angiography of chest
   - Blood pressure control (target SBP <120)
   - Emergent vascular/cardiac surgery consultation
4. If non-acute:
   - Echocardiogram to assess cardiac chambers
   - CT chest with contrast for mediastinal evaluation
   - Consider lymphoma workup if anterior mediastinal mass

Differential Diagnoses:
- Cardiomegaly
- Aortic aneurysm or dissection
- Mediastinal mass (lymphoma, thymoma, goiter)
- Pericardial effusion
- Hiatal hernia
- Technical factors (AP view, rotation, obesity)

Urgency: Emergent if acute aortic syndrome; Semi-urgent otherwise
Specialty Referral: Cardiology, Vascular Surgery, or Oncology as appropriate
ICD-10 Codes: R93.1 (Abnormal findings on diagnostic imaging of heart)
        """,
        "urgency": "semi-urgent",
        "specialty": "cardiology"
    },
    {
        "id": "lung_opacity_001",
        "pathology": "Lung Opacity",
        "content": """
LUNG OPACITY - Clinical Recommendations

Definition:
Non-specific term for any area of increased attenuation in the lung. 
Encompasses consolidation, ground-glass opacity, nodules, and masses.

Clinical Significance:
- Broad differential requiring clinical correlation
- Pattern recognition helps narrow differential
- May require CT for better characterization

Recommended Actions:
1. Characterize the opacity (location, size, pattern, distribution)
2. Correlate with clinical symptoms
3. Review prior imaging for comparison
4. Consider CT chest for indeterminate opacities
5. Laboratory workup based on clinical suspicion
6. Follow-up imaging to assess resolution or progression

Differential Diagnoses:
- Infectious (pneumonia, TB, fungal)
- Inflammatory (organizing pneumonia, eosinophilic)
- Neoplastic (primary or metastatic)
- Vascular (pulmonary embolism with infarct)
- Aspiration
- Atelectasis

Urgency: Varies based on clinical context
Specialty Referral: Pulmonology if unclear etiology
ICD-10 Codes: R91.8 (Other nonspecific abnormal finding of lung)
        """,
        "urgency": "routine",
        "specialty": "pulmonology"
    },
    {
        "id": "fracture_001",
        "pathology": "Fracture",
        "content": """
RIB FRACTURE - Clinical Recommendations

Definition:
Break in rib continuity, often seen as cortical disruption or displacement 
on chest radiograph. May be subtle or occult on plain films.

Clinical Significance:
- Often result of trauma; pathologic fractures suggest metastatic disease
- Multiple rib fractures increase risk of pulmonary complications
- Flail chest (3+ consecutive ribs fractured in 2 places) is serious

Recommended Actions:
1. Assess for adequate pain control (multimodal analgesia)
2. Incentive spirometry to prevent atelectasis and pneumonia
3. CT chest if:
   - Multiple fractures suspected
   - Concern for underlying lung injury
   - Elderly patient with high-energy mechanism
4. Assess for associated injuries (pneumothorax, hemothorax)
5. Surgical fixation consideration for flail chest or displaced fractures
6. If no trauma, evaluate for pathologic fracture (bone scan, oncology)

Pain Management:
- NSAIDs and acetaminophen
- Consider intercostal nerve block for severe pain
- Avoid oversedation (risk of hypoventilation)

Urgency: Urgent if multiple fractures or associated injuries
Specialty Referral: Trauma Surgery if severe; Oncology if pathologic
ICD-10 Codes: S22.3 (Fracture of rib)
        """,
        "urgency": "semi-urgent",
        "specialty": "trauma_surgery"
    },
    {
        "id": "support_devices_001",
        "pathology": "Support Devices",
        "content": """
SUPPORT DEVICES - Clinical Recommendations

Definition:
Medical devices visible on chest radiograph including endotracheal tubes, 
central lines, chest tubes, pacemakers, and feeding tubes.

Clinical Significance:
- Position verification is critical for patient safety
- Malpositioned devices can cause serious complications
- Part of routine ICU chest radiograph interpretation

Recommended Actions:

ENDOTRACHEAL TUBE:
- Tip should be 3-5 cm above carina (T2-T4 level)
- Right mainstem intubation if too low
- Risk of extubation if too high

CENTRAL VENOUS CATHETER:
- Tip should be at cavoatrial junction or SVC
- Check for pneumothorax post-insertion
- Malposition may cause arrhythmia or perforation

NASOGASTRIC/FEEDING TUBE:
- Tip should be below diaphragm in stomach
- NEVER use if positioned in airway

CHEST TUBE:
- Should be within pleural space
- All drainage holes within thorax
- Check for resolution of pneumothorax/effusion

PACEMAKER/ICD:
- Leads should be in appropriate cardiac chambers
- Check for lead fracture or displacement

Urgency: Urgent if malpositioned
Specialty Referral: Notify primary team immediately if malposition
ICD-10 Codes: T85.9 (Complication of internal prosthetic device)
        """,
        "urgency": "urgent",
        "specialty": "critical_care"
    }
]


def get_all_pathologies() -> List[str]:
    """Return list of all pathology names in the knowledge base."""
    return [doc["pathology"] for doc in PATHOLOGY_RECOMMENDATIONS]


def get_recommendation_by_pathology(pathology: str) -> Dict:
    """Get recommendation document for a specific pathology."""
    for doc in PATHOLOGY_RECOMMENDATIONS:
        if doc["pathology"].lower() == pathology.lower():
            return doc
    return None


def get_recommendations_by_urgency(urgency: str) -> List[Dict]:
    """Get all recommendations with a specific urgency level."""
    return [doc for doc in PATHOLOGY_RECOMMENDATIONS if doc["urgency"] == urgency]

