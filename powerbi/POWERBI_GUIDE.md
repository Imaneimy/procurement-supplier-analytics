# Guide Power BI — Procurement & Supplier Performance

Temps estimé : 2 à 3 heures. À la fin tu as un fichier `procurement_dashboard.pbix` avec 4 pages et des mesures validées contre le SQL.

## 0. Préparer les données

```bash
cd src
python generate_data.py
python run_pipeline.py      # écrit les 6 tables dans powerbi/data/
```

## 1. Importer (Power Query)

1. Power BI Desktop → **Accueil › Transformer les données**.
2. **Gérer les paramètres › Nouveau** : `DataFolder` (Texte) = chemin complet de `powerbi/data/` **avec le `\` final**.
3. Pour chaque bloc de `power_query.m` : **Nouvelle source › Requête vide › Éditeur avancé**, coller, renommer la requête (`fact_purchase_order`, `fact_budget`, `dim_supplier`, `dim_department`, `dim_date`, `dq_results`).
4. **Fermer et appliquer**.
5. **Affichage › Thèmes › Parcourir** → `procurement_theme.json`.

## 2. Modèle en étoile (vue Modèle)

| De (plusieurs) | Vers (un) | Filtre |
|---|---|---|
| `fact_purchase_order[order_date]` | `dim_date[Date]` | simple |
| `fact_purchase_order[supplier_id]` | `dim_supplier[supplier_id]` | simple |
| `fact_purchase_order[department]` | `dim_department[department]` | simple |
| `fact_budget[quarter_start]` | `dim_date[Date]` | simple |
| `fact_budget[department]` | `dim_department[department]` | simple |

Puis :
- `dim_date` → clic droit › **Marquer comme table de dates** (colonne `Date`).
- `dim_date[Month]` → **Trier par colonne** `MonthNumber`.
- Masquer les clés côté fait (`supplier_id`, `department`, `order_date`, `quarter_start`) pour forcer l'usage des dimensions.

## 3. Mesures DAX

Créer une table `_Measures` (**Accueil › Entrer des données**, valider vide), puis ajouter chaque mesure de `measures.dax`. Ranger en dossiers d'affichage : *Spend, Delivery, Invoices, Supplier, Budget, Data Quality*.

Formats : `%` pour On-Time / Invoice Match / Quality Issue / Off-Contract / Budget Consumed / YoY, `0.0` pour les délais, `#,0` pour les montants.

## 4. Les 4 pages

### Page 1 — Overview
```
┌──────────────────────────────────────────────────────────────────────┐
│ Procurement & Supplier Performance        [Segment: Année] [Dépt]    │
├──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┤
│Spend (M) │ PO Count │ On-Time %│Lead Time │Inv Match%│Off-Contract % │  ← 6 cartes
├──────────┴──────────┴──────────┴──────────┴──────────┴───────────────┤
│ ⚠ [Attention Headline]                                    (carte)    │
├─────────────────────────────────────────┬────────────────────────────┤
│ Histogramme + courbe :                  │ Barres : Total Spend       │
│ Axe dim_date[YearMonth]                 │ par fact[category]         │
│ Colonnes [Spend (M MAD)]                │                            │
│ Ligne [On-Time %]                       │                            │
└─────────────────────────────────────────┴────────────────────────────┘
```

### Page 2 — Suppliers
```
┌──────────────────────────────────────────────────────────────────────┐
│ [Segment: catégorie] [Segment: ville] [Segment: contrat cadre]       │
├─────────────────────────────────────────┬────────────────────────────┤
│ Pareto (histogramme + courbe) :         │ Matrice scorecard :        │
│ Axe dim_supplier[supplier_id]           │ supplier_id, category,     │
│ trié par Total Spend décroissant        │ PO Count, Spend, On-Time %,│
│ Colonnes [Total Spend]                  │ Quality Issue %,           │
│ Ligne [Cumulative Spend %]              │ Invoice Match %,           │
│ + ligne constante 80 % (Analytique)     │ Supplier Score             │
├─────────────────────────────────────────┤ → Mise en forme cond. :    │
│ Nuage de points : X On-Time %,          │   couleur d'arrière-plan   │
│ Y Invoice Match %, taille Total Spend   │   = valeur du champ        │
│ → les fournisseurs en bas à gauche      │   [Score Color]            │
│   sont ceux à appeler                   │                            │
└─────────────────────────────────────────┴────────────────────────────┘
```

### Page 3 — Budget
- Barres horizontales : `dim_department[department]` × `[Budget Consumed %]`, couleur des barres via **fx** → `[Budget Color]`, ligne constante à 100 %.
- Histogramme groupé : `dim_date[YearQuarter]` × `[Budget]` et `[Total Spend]`.
- Cartes : `[Departments Over Budget]`, `[Budget Variance]`, `[Spend YoY %]`.

### Page 4 — Data Quality
- Cartes : `[DQ Checks Passed]` / `[DQ Checks]`, `[DQ Rows Fixed]`.
- Tableau `dq_results` (check_id, rule, rows_failed, pct_failed, status), colonne `status` colorée avec `[DQ Status Color]`.
- Texte : *« Les données sont contrôlées avant chaque rafraîchissement : doublons supprimés, montants corrigés, écarts facture signalés au métier. »*

**Bonus pro :** une info-bulle (page Tooltip) sur la matrice fournisseurs avec la tendance mensuelle On-Time % du fournisseur survolé, et des boutons de navigation entre les pages.

## 5. Valider les mesures (réflexe testeur)

Sans aucun filtre, chaque mesure doit retrouver la valeur calculée en SQL par `run_pipeline.py` :

| ID | Mesure | Valeur attendue |
|---|---|---|
| TC-BI-01 | Total Spend | 1 335,9 M MAD |
| TC-BI-02 | PO Count | 6 000 |
| TC-BI-03 | On-Time % | 78,0 % |
| TC-BI-04 | Avg Lead Time | 27,3 j |
| TC-BI-05 | Invoice Match % | 89,7 % |
| TC-BI-06 | Overbilled Amount | 11,87 M MAD |
| TC-BI-07 | Off-Contract Spend % | 9,6 % |
| TC-BI-08 | Departments Over Budget | 4 (Network 115 %, General Services 114 %, Finance 112 %, Customer Care 107 %) |
| TC-BI-09 | Open POs | 150 |
| TC-BI-11 | Suppliers for 80% of Spend | 20 |
| TC-BI-10 | Spend YoY % (filtre Jan–Juin 2025) | +3,8 % (449,3 vs 432,9 M) |

Mets ce tableau avec une colonne « Résultat Power BI » dans le README : c'est la preuve que ton dashboard est juste.

## 6. Pour GitHub et le portfolio

- Enregistrer `procurement_dashboard.pbix` dans `powerbi/`.
- **Exporter › PDF** → `reports/procurement_dashboard.pdf`.
- Capture de chaque page → `reports/screenshots/01_overview.png`, `02_suppliers.png`, `03_budget.png`, `04_data_quality.png` (déjà référencées dans le README).
- Image de couverture du portfolio : `01_overview.png`.
