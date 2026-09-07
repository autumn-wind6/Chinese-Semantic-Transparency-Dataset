#!/usr/bin/env Rscript

# Test lexical-structure main effects and ST-by-structure interaction.
suppressPackageStartupMessages(library(readxl))
suppressPackageStartupMessages(library(writexl))

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1]]), mustWork = FALSE))
repo_root <- normalizePath(file.path(script_dir, ".."), mustWork = FALSE)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 3) stop("usage: Rscript s2_structure_incremental_variance.R [BEHAVIOR.xlsx] [STRUCTURE.xlsx] [OUTPUT_DIR]")
behavior_path <- if (length(args) >= 1) args[[1]] else file.path(repo_root, "data", "input", "behavioral_variance_input.xlsx")
structure_path <- if (length(args) >= 2) args[[2]] else file.path(repo_root, "data", "final", "chinese_semantic_transparency_lexicon.xlsx")
output_dir <- if (length(args) >= 3) args[[3]] else file.path(repo_root, "results")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

behavior <- as.data.frame(read_excel(behavior_path))
controls_all <- c("LogWF", "Stroke", "C1.LogCF", "C2.LogCF", "C1.LogFS.Type", "C2.LogFS.Type", "C1.LogNoM", "C2.LogNoM", "C1.LogNoP", "C2.LogNoP")
controls <- c("LogWF", "Stroke", "C1.LogCF", "C2.LogCF", "C1.LogFS.Type", "C2.LogFS.Type", "C2.LogNoM", "C1.LogNoP")
required <- c("Word", "Real", "zRT", "ERR", controls_all, "C1.ST_qwen", "C2.ST_qwen")
behavior <- behavior[behavior$ERR <= 30 & behavior$Real == 1, required]
behavior <- behavior[complete.cases(behavior), ]
for (name in c(controls_all, "C1.ST_qwen", "C2.ST_qwen")) behavior[[name]] <- as.numeric(scale(behavior[[name]], center = TRUE, scale = FALSE))

formula_from <- function(response, predictors) as.formula(paste(response, "~", paste(predictors, collapse = " + ")))
initial <- lm(formula_from("zRT", controls_all), data = behavior)
behavior <- behavior[abs(as.numeric(scale(residuals(initial)))) < 2.5, ]

structure <- if (grepl("\\.csv$", structure_path, ignore.case = TRUE)) {
  read.csv(structure_path, check.names = FALSE)
} else {
  as.data.frame(read_excel(structure_path))
}
word_col <- if ("Word" %in% names(structure)) "Word" else "word"
label_col <- if ("词汇结构" %in% names(structure)) "词汇结构" else "lexical_structure"
c1_col <- if ("C1_ST_qwen" %in% names(structure)) "C1_ST_qwen" else if ("C1_ST" %in% names(structure)) "C1_ST" else "qwen_c1_score"
c2_col <- if ("C2_ST_qwen" %in% names(structure)) "C2_ST_qwen" else if ("C2_ST" %in% names(structure)) "C2_ST" else "qwen_c2_score"
structure <- structure[, c(word_col, label_col, c1_col, c2_col)]
names(structure) <- c("Word", "LexicalStructure", "Qwen_C1", "Qwen_C2")
label_map <- c(
  "联合" = "COORD", "偏正" = "SUBORD", "主谓" = "SP", "补充" = "COMP",
  "动宾" = "VO", "前缀" = "PFX", "后缀" = "SFX", "音译外来词" = "PLW",
  "叠音" = "PHON_RED", "重叠" = "MORPH_RED", "连绵词" = "BINOME"
)
mapped <- unname(label_map[as.character(structure$LexicalStructure)])
structure$LexicalStructure <- ifelse(is.na(mapped), as.character(structure$LexicalStructure), mapped)
valid_labels <- c("COORD", "SUBORD", "COMP", "VO", "SP", "PHON_RED", "MORPH_RED", "BINOME", "PLW", "PFX", "SFX")
structure <- structure[structure$LexicalStructure %in% valid_labels, ]
structure$SemTrans_Mean <- (structure$Qwen_C1 + structure$Qwen_C2) / 2

analysis <- merge(behavior, structure, by = "Word")
analysis <- analysis[complete.cases(analysis), ]
reference <- if ("SUBORD" %in% analysis$LexicalStructure) "SUBORD" else "偏正"
analysis$LexicalStructure <- relevel(factor(analysis$LexicalStructure), ref = reference)
analysis$SemTrans_Mean_c <- as.numeric(scale(analysis$SemTrans_Mean, center = TRUE, scale = FALSE))
if (nrow(analysis) != 8401) warning(sprintf("expected 8,401 rows, found %s", nrow(analysis)))

summary_rows <- list()
comparison_rows <- list()
for (outcome in c("zRT", "ERR")) {
  control <- lm(formula_from(outcome, controls), data = analysis)
  structure_only <- lm(formula_from(outcome, c(controls, "LexicalStructure")), data = analysis)
  main <- lm(formula_from(outcome, c(controls, "SemTrans_Mean_c", "LexicalStructure")), data = analysis)
  interaction <- lm(formula_from(outcome, c(controls, "SemTrans_Mean_c * LexicalStructure")), data = analysis)
  fits <- list(control = control, structure = structure_only, main_effects = main, interaction = interaction)
  for (name in names(fits)) {
    fit <- fits[[name]]
    summary_rows[[length(summary_rows) + 1]] <- data.frame(
      outcome = outcome, model = name, n = nobs(fit), r2 = summary(fit)$r.squared,
      adjusted_r2 = summary(fit)$adj.r.squared, AIC = AIC(fit), BIC = BIC(fit)
    )
  }
  pairs <- list(c("control", "structure"), c("control", "main_effects"), c("main_effects", "interaction"))
  for (pair in pairs) {
    cmp <- anova(fits[[pair[[1]]]], fits[[pair[[2]]]])
    comparison_rows[[length(comparison_rows) + 1]] <- data.frame(
      outcome = outcome, reduced_model = pair[[1]], full_model = pair[[2]],
      df = cmp$Df[2], F = cmp$F[2], p_value = cmp$`Pr(>F)`[2]
    )
  }
}
model_summary <- do.call(rbind, summary_rows)
comparisons <- do.call(rbind, comparison_rows)
write_xlsx(model_summary, file.path(output_dir, "structure_model_comparison.xlsx"))
write_xlsx(comparisons, file.path(output_dir, "structure_nested_tests.xlsx"))
print(model_summary, digits = 6)
print(comparisons, digits = 6)
