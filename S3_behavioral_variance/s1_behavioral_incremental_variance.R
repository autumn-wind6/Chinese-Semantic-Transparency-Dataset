#!/usr/bin/env Rscript

# Reproduce incremental explained-variance analyses for zRT and ERR.
suppressPackageStartupMessages(library(readxl))

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1]]), mustWork = FALSE))
repo_root <- normalizePath(file.path(script_dir, ".."), mustWork = FALSE)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 2) stop("usage: Rscript s1_behavioral_incremental_variance.R [INPUT.xlsx] [OUTPUT_DIR]")
input_path <- if (length(args) >= 1) args[[1]] else file.path(repo_root, "data", "input", "behavioral_variance_input.xlsx")
output_dir <- if (length(args) >= 2) args[[2]] else file.path(repo_root, "results")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

data <- as.data.frame(read_excel(input_path))
controls_all <- c("LogWF", "Stroke", "C1.LogCF", "C2.LogCF", "C1.LogFS.Type", "C2.LogFS.Type", "C1.LogNoM", "C2.LogNoM", "C1.LogNoP", "C2.LogNoP")
controls_final <- c("LogWF", "Stroke", "C1.LogCF", "C2.LogCF", "C1.LogFS.Type", "C2.LogFS.Type", "C2.LogNoM", "C1.LogNoP")
metrics <- c("C1.ST", "C2.ST", "C1.ST_qwen", "C2.ST_qwen", "human_average", "qwen_average")
required <- c("Word", "C1", "C2", "Real", "zRT", "ERR", controls_all, metrics)
missing <- setdiff(required, names(data))
if (length(missing)) stop(paste("missing columns:", paste(missing, collapse = ", ")))

data <- data[data$ERR <= 30 & data$Real == 1, required]
data <- data[complete.cases(data), ]
initial_n <- nrow(data)
for (name in c(controls_all, metrics)) data[[name]] <- as.numeric(scale(data[[name]], center = TRUE, scale = FALSE))

formula_from <- function(response, predictors) as.formula(paste(response, "~", paste(predictors, collapse = " + ")))
initial_fit <- lm(formula_from("zRT", controls_all), data = data)
keep <- abs(as.numeric(scale(residuals(initial_fit)))) < 2.5
analysis <- data[keep, ]
if (nrow(analysis) != 8402) warning(sprintf("expected 8,402 rows, found %s", format(nrow(analysis), big.mark = ",")))

model_specs <- list(
  baseline = controls_final,
  human_st = c(controls_final, "C1.ST", "C2.ST"),
  qwen_st = c(controls_final, "C1.ST_qwen", "C2.ST_qwen"),
  human_and_qwen_st = c(controls_final, "C1.ST", "C2.ST", "C1.ST_qwen", "C2.ST_qwen")
)

rows <- list()
for (response in c("zRT", "ERR")) {
  fits <- lapply(model_specs, function(predictors) lm(formula_from(response, predictors), data = analysis))
  baseline <- fits[["baseline"]]
  for (model_name in names(fits)) {
    fit <- fits[[model_name]]
    nested_f <- nested_df <- nested_p <- NA_real_
    if (model_name != "baseline") {
      cmp <- anova(baseline, fit)
      nested_df <- cmp$Df[2]
      nested_f <- cmp$F[2]
      nested_p <- cmp$`Pr(>F)`[2]
    }
    rows[[length(rows) + 1]] <- data.frame(
      outcome = response, model = model_name, n = nobs(fit),
      r2 = summary(fit)$r.squared, adjusted_r2 = summary(fit)$adj.r.squared,
      delta_r2 = summary(fit)$r.squared - summary(baseline)$r.squared,
      delta_adjusted_r2 = summary(fit)$adj.r.squared - summary(baseline)$adj.r.squared,
      AIC = AIC(fit), BIC = BIC(fit), nested_df = nested_df,
      nested_F = nested_f, nested_p = nested_p
    )
  }
}
result <- do.call(rbind, rows)
write.csv(result, file.path(output_dir, "behavioral_model_comparison.csv"), row.names = FALSE)
write.csv(data.frame(initial_complete_cases = initial_n, excluded_by_zrt_residual = sum(!keep), analysis_n = nrow(analysis)), file.path(output_dir, "behavioral_sample_audit.csv"), row.names = FALSE)
print(result, digits = 6)
