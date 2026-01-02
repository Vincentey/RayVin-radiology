from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from .stateclass import AgentState
from .relevance_checker import DicomProcessor
from .tensor_presenter import TensorPresenter
from .ct_mri_presenter import get_ct_mri_presenter
from .rag_pipeline import get_rag_pipeline

# X-ray: TorchXRayVision DenseNet-121 (trained on ChestX-ray14, CheXpert, MIMIC-CXR)
_xray_presenter = TensorPresenter(model_name="densenet121-res224-all")

workflow = StateGraph(AgentState)

def relevance_gateway (state: AgentState):
     path_list= state["dicom_path"]
     processor= DicomProcessor(path_list)
     mod= processor.ModalityRelevance() 
     
     if mod.get("is_relevant") == False:
          return mod
     else: 
          meta= processor.ExtractMetadata()
          return mod|meta


def router1 (state:AgentState):
     if state["is_relevant"] == False:
          return END
     if state["is_relevant"]== True and state["modality"] in ["CR", "DX"]:
          return "Xray"
     if state["is_relevant"]== True and state["modality"] in ["CT", "MR"]:
          return "CT/MRI"


def preprocess_xray (state:AgentState):
     path_list = state["dicom_path"]
     processor= DicomProcessor(path_list)
     return processor.Image_extractor()


def xray_vision_model(state: AgentState):
     """Present X-ray tensors to DenseNet-121 and generate Grad-CAM heatmaps."""
     image_tensors = state.get("image_tensor")
     if image_tensors is None:
          return {"model_predictions": None, "gradcam_heatmaps": None}
     
     result = _xray_presenter.xray_densenet_gradcam(
          image_tensors=image_tensors,
          threshold=0.65,  # 65% confidence required for positive findings
          top_k=5,
          generate_heatmaps=True
     )
     
     return {
          "model_predictions": result.get("predictions"),
          "gradcam_heatmaps": result.get("heatmaps")
     }


def ct_mri_guard(state:AgentState):
      path_list = state["dicom_path"]
      processor= DicomProcessor(path_list)
      return processor.guardrail()

def router2 (state:AgentState):
     if state.get("is_relevant") == True:
          return "valid"
     return "invalid"
     
def tensor_formation(state: AgentState):
     """Extract and preprocess 3D volume from CT/MRI DICOM slices."""
     path_list = state["dicom_path"]
     processor = DicomProcessor(path_list)
     result = processor.Image_extractor_3D()
     
     # Handle errors from Image_extractor_3D
     if "error" in result:
          print(f"CT/MRI preprocessing error: {result['error']}")
          return {"volume_tensor": None, "preprocessing_error": result["error"]}
     
     return result


def ct_mri_vision_model(state: AgentState):
     """Present CT/MRI volume to 3D DenseNet model."""
     volume_tensor = state.get("volume_tensor")
     modality = state.get("modality", "CT")
     
     # Check for preprocessing errors
     if state.get("preprocessing_error"):
          return {"model_predictions": None, "error": state["preprocessing_error"]}
     
     if volume_tensor is None:
          return {"model_predictions": None}
     
     try:
          presenter = get_ct_mri_presenter()
          result = presenter.analyze_volume(
               volume_tensor=volume_tensor,
               modality=modality,
               threshold=0.5,
               top_k=5
          )
          return {"model_predictions": [result.get("predictions")]}
     except Exception as e:
          print(f"CT/MRI model error: {e}")
          return {"model_predictions": None, "error": str(e)}


def rag_recommendations(state: AgentState):
     """Generate clinical recommendations using RAG pipeline based on X-ray findings."""
     predictions = state.get("model_predictions")
     
     if not predictions or len(predictions) == 0:
          return {"clinical_recommendations": None}
     
     # Extract findings from predictions
     all_findings = []
     finding_probabilities = {}
     
     for prediction in predictions:
          positive_findings = prediction.get("positive_findings", [])
          top_predictions = prediction.get("top_predictions", [])
          
          all_findings.extend(positive_findings)
          
          # Build probability dict from top predictions
          for finding, prob in top_predictions:
               if finding not in finding_probabilities:
                    finding_probabilities[finding] = prob
     
     # Remove duplicates while preserving order
     unique_findings = list(dict.fromkeys(all_findings))
     
     if not unique_findings:
          # If no positive findings, use top predictions
          for prediction in predictions:
               for finding, prob in prediction.get("top_predictions", [])[:3]:
                    if finding not in unique_findings:
                         unique_findings.append(finding)
     
     if not unique_findings:
          return {"clinical_recommendations": None}
     
     # Get RAG pipeline and generate recommendations
     try:
          rag = get_rag_pipeline()
          
          # Handle case when RAG pipeline is unavailable (missing API keys)
          if rag is None:
               print("RAG pipeline unavailable - returning findings without recommendations")
               return {
                    "clinical_recommendations": {
                         "findings": unique_findings,
                         "recommendations": "RAG pipeline unavailable. Please verify API keys are configured.",
                         "overall_urgency": "unknown",
                         "error": "RAG pipeline not initialized - check OPENAI_API_KEY and PINECONE_API_KEY"
                    }
               }
          
          recommendations = rag.generate_recommendations(
               findings=unique_findings,
               finding_probabilities=finding_probabilities
          )
          return {"clinical_recommendations": recommendations}
     except Exception as e:
          print(f"RAG pipeline error: {e}")
          return {
               "clinical_recommendations": {
                    "findings": unique_findings,
                    "recommendations": f"Error generating recommendations: {str(e)}",
                    "overall_urgency": "unknown",
                    "error": str(e)
               }
          }


workflow.add_node("rg", relevance_gateway)
workflow.add_node("px", preprocess_xray)
workflow.add_node("xvm", xray_vision_model)  # X-ray vision model node
workflow.add_node("rag", rag_recommendations)  # RAG recommendations node
workflow.add_node("cmg", ct_mri_guard)
workflow.add_node("tf", tensor_formation)
workflow.add_node("ctvm", ct_mri_vision_model)  # CT/MRI vision model node

workflow.set_entry_point("rg")
workflow.add_conditional_edges("rg", router1, {"Xray":"px", "CT/MRI":"cmg", END: END})
workflow.add_edge("px", "xvm")
workflow.add_edge("xvm", "rag")

workflow.add_conditional_edges("cmg", router2, {"valid":"tf", "invalid": END})
workflow.add_edge("tf", "ctvm")
workflow.add_edge("ctvm", "rag")

wapp = workflow.compile()


# Extract findings and recommendations from the result
def extract_output(state):
    """Extract findings and recommendations from the workflow result."""
    output = {}
    
    # Extract findings
    if state.get("model_predictions"):
        findings = []
        for prediction in state["model_predictions"]:
            findings.append({
                "positive_findings": prediction.get("positive_findings", []),
                "top_predictions": prediction.get("top_predictions", [])
            })
        output["findings"] = findings
    
    # Extract recommendations
    if state.get("clinical_recommendations"):
        recs = state["clinical_recommendations"]
        output["recommendations"] = recs.get("recommendations")
        output["urgency"] = recs.get("overall_urgency")
    
    return output if output else state


# CLI test function (only runs when executed directly)
def _run_test():
    """Test the workflow with a sample DICOM file."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m radio_assistance.mainapp.the_nodes <dicom_path>")
        return
    
    dicom_path = sys.argv[1]
    print(f"Testing with: {dicom_path}")
    
    result = wapp.invoke({"dicom_path": [dicom_path]})
    output = extract_output(result)
    
    if "findings" in output:
        print("\n" + "="*60)
        print("FINDINGS")
        print("="*60)
        for i, finding in enumerate(output["findings"]):
            print(f"\nImage {i+1}:")
            print(f"  Positive Findings: {finding['positive_findings']}")
            print(f"  Top Predictions: {finding['top_predictions'][:3]}")
    
    if "recommendations" in output:
        print("\n" + "="*60)
        print(f"CLINICAL RECOMMENDATIONS (Urgency: {output.get('urgency', 'N/A')})")
        print("="*60)
        print(output["recommendations"])


if __name__ == "__main__":
    _run_test()

