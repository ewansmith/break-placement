# Break-Placement
Generate metadata from video content to be used in choice of break / ad placement in media

Created as PoC project with ITV which forms basis of UCL MSc Computer Science Dissertation.

## What Does It Do

Production id used to query APIs for relevant information. This is used alongside ffmpeg to output 3 datapoints:
Volume, Black Frames and Distribution Score

These datapoints are to be used, with the break points chosen by ITV Compliance as targets, as features to train a Machine Learning model to predict optimal break point insertion.

## How to use

main.py -> Runs main metadata production pipeline

predictions.py -> Uses model endpoint to generate predictions on ids

results.py -> Calculates success rate of predictions
