# Dataset inclus — TrashNet

La distribution complète (`YOLO_Waste_Detection_Kit.zip`) contient le dataset sous `data/raw/dataset-resized/`, avec 2 527 images JPEG réparties dans six dossiers :

| Classe | Images |
|---|---:|
| cardboard | 403 |
| glass | 501 |
| metal | 410 |
| paper | 594 |
| plastic | 482 |
| trash | 137 |
| **Total** | **2 527** |

Source : Gary Thung et Mindy Yang, <https://github.com/garythung/trashnet>. Licence MIT jointe à `TRASHNET_LICENSE.txt`; conserver l'attribution.

Ces images possèdent une étiquette par image, pas des boîtes. Elles servent à la classification détaillée des crops; elles ne constituent pas le dataset d'entraînement du détecteur de boîtes. Le dossier de travail peut omettre la copie extraite des images; la distribution ZIP complète les contient.
