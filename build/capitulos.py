# Clasificación de incidencias por capítulo (programa)
CAP = {
 'imagen':   [266,181,408,449,450,353,174,384,431,382,316,387,379,383,218,219,234],
 'alberca':  [236,326,327,324,335,411,445,446,462,1,430,457,357,351,188,287,269,250,336,255,319],
 'agua':     [373,397,400,467,451,262,370,415,308,425,426],
 'seguridad':[252,210,235,278,279,280,281,342,434,435,455,200,206,253,254,265,388,454,465,249,418],
 'unidades': [182,190,377,362,366,368,401,220,222,225,227,229,304,340,376,469,195,217,223,303,354,
              203,283,284,285,317,348,360,378,385,417,448,183,201,209,231,232,310,364,389,433,374,267,386,463,464,
              226,228,289,175,179,180,191,345,241,307,258,311,416,466,202,256,257],
 'exterior': [189,442,248,268,288,349,361,381,398,407,413,432,439,453,443,247,369,441,456,337,352,244,302,459,419,460,458,447,263,216,344,339,341,338,365],
 'huesped':  [355],
}
EXCLUIR = [10, 245, 292, 204]   # 2024 migrada; multa de playa (no es mantenimiento)
TITULOS = {
 'imagen':'Renovación de imagen', 'alberca':'Alberca y jacuzzi', 'agua':'Lluvias, humedad y filtraciones',
 'seguridad':'Seguridad y accesos', 'unidades':'Dentro de las unidades', 'exterior':'Limpieza, jardín y áreas comunes', 'huesped':'Hospitalidad',
}
ID2CAP = {i:c for c,ids in CAP.items() for i in ids}
