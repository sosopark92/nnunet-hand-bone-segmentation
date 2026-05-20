# Dataset
The dataset used in this study consists of hand and wrist CT scans obtained from the KU Leuven Research Data Repository. It contains high-resolution CT images and associated anatomical data of the hand and wrist region.  

Available at: https://rdr.kuleuven.be/dataset.xhtml?persistentId=doi:10.48804/DWF4RG  

# Methods

## Original Baseline
<img src="./image/inference_img_origin.png" width="60%">  
- Standarise the hand CT images, flipped them into consistant l or R. 
- Fully segmented hand CT
- Normal nnU-Net 3d_fullres
- Trained/tested as a standard whole-volume multi-class segmentation experiment

Adding a 2-step strategy because the current result showed:
- Small bones, especially around the metacarpal area, were segmented fairly well
- Larger bones were not segmented as well


🟥 The model may already be good at local detail, but weaker at global anatomical context / extent.

## 2-Stage Experiment

**🟦 Target**  
I need the thumb area to be segmented very accurately. but I also want better whole-hand segmentation.  

**🟩 The 3 ROI groups**
1. thumb (Trapezium + Scaphoid + Metacarpal1): thumb gets its own focused region
2. middle phalanx 2–5 + distal phalanx 1-5 + proximal phalanx 1-5 + metacarpals: fingers/metacarpals are grouped into another region
3. carpals + distal radius/ulna: wrist/carpal area gets its own region because it is complex


**1️⃣ Stage 1: Coarse Segmentation**  
1. Find the defined groups of ROIs    
2. From the original multi-class mask, create a binary ROI mask for each group  
- Thumb labels → one binary thumb ROI mask  
- Digits/metacarpals labels → one binary ROI mask  
- Carpals/wrist labels → one binary ROI mask  
3. Use that ROI mask to:
- compute a bounding box  
📌 what is a bouding box?  
    - A bounding box is the smallest box that contains the foreground mask.
4. Add a margin  
📌 Why do we add a margin around the bbox?
    - the bone may touch the crop boundary
    - some useful surrounding anatomy may be lost
    - the model may not get enough context
    - prediction may become unstable
5. Crop the original CT
- Crop the original multi-class mask
- Save each group as a new nnU-Net dataset

*The ROI comes from the ground-truth label*  
*The goal is to test whether ROI-specific cropping helps*  


**2️⃣ Stage 2: Fine Segmentation**  
1. Use Stage 1 ROI crops as input. The cropped CT volumes from each ROI group are used as separate training inputs.
2. Train ROI-specific nnU-Net models. Each ROI is trained independently:  
    - Thumb ROI model
    - Fingers/Metacarpals ROI model
    - Wrist/Carpal ROI model
3. Perform fine multi-class segmentation inside each ROI.  
    - Instead of segmenting the whole hand at once, the model focuses only on the bones inside a smaller anatomical region. This allows the network to learn finer local details, especially for small or complex bones.  
4. Improve thumb-region accuracy.
    - The thumb ROI is treated as a priority region: Trapezium, Scaphoid, First metacarpal  
5. Map ROI predictions back to the original CT space. 
    - After prediction, each ROI segmentation is placed back into its original location using the saved bounding box coordinates.   
6. Merge ROI predictions into a whole-hand segmentation. The three ROI outputs are combined to reconstruct the final full hand/wrist segmentation.   
7. Compare with the original whole-volume baseline.  
8. The ROI-based method will be evaluated against the original standard nnU-Net whole-volume model to check whether it improves:  
- Thumb segmentation accuracy  
- Small bone segmentation   
- Overall whole-hand segmentation quality  
