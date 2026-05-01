if (!requireNamespace("lintr", quietly = TRUE)) {
  stop("Package 'lintr' is required.")
}
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Package 'jsonlite' is required.")
}

slice_root <- normalizePath(Sys.getenv("LINTR_SLICE_ROOT"), winslash = "/", mustWork = TRUE)
out_json <- Sys.getenv("LINTR_OUT_JSON")
repo_root <- normalizePath(Sys.getenv("LINTR_REPO_ROOT"), winslash = "/", mustWork = TRUE)
if (!nzchar(out_json)) {
  stop("LINTR_OUT_JSON must be set.")
}

resolve_issue_path <- function(path) {
  # lintr may return absolute paths or paths relative to the linted slice.
  if (grepl("^(/|[A-Za-z]:[/\\\\])", path)) {
    path
  } else {
    file.path(slice_root, path)
  }
}

to_slice_rel <- function(path) {
  # Sonar external issues need paths relative to the scanner's slice root.
  p <- normalizePath(path, winslash = "/", mustWork = FALSE)
  if (startsWith(p, slice_root)) {
    sub(paste0("^", slice_root, "/?"), "", p)
  } else {
    p
  }
}

linters <- lintr::lint_dir(slice_root)
issues <- list()
line_cache <- new.env(parent = emptyenv())

for (i in seq_along(linters)) {
  lint <- linters[[i]]
  source_path <- resolve_issue_path(lint$filename)
  filename <- to_slice_rel(source_path)
  line <- ifelse(is.null(lint$line_number) || is.na(lint$line_number), 1L, as.integer(lint$line_number))
  col <- ifelse(is.null(lint$column_number) || is.na(lint$column_number), 1L, as.integer(lint$column_number))

  # Cache file contents because many lint findings can point to the same file.
  if (!exists(filename, envir = line_cache, inherits = FALSE)) {
    file_lines <- tryCatch(readLines(source_path, warn = FALSE), error = function(e) character())
    assign(filename, file_lines, envir = line_cache)
  }

  file_lines <- get(filename, envir = line_cache, inherits = FALSE)
  line_count <- length(file_lines)
  if (line_count <= 0L) {
    line <- 1L
    text_range <- NULL
  } else {
    line <- max(1L, min(line, line_count))
    line_text <- file_lines[[line]]
    line_width <- nchar(line_text, type = "chars", allowNA = FALSE, keepNA = FALSE)

    if (line_width <= 0L) {
      text_range <- NULL
    } else {
      # Sonar uses zero-based columns in external issue text ranges.
      start_offset <- max(0L, col - 1L)
      start_offset <- min(start_offset, line_width - 1L)
      end_offset <- min(line_width, start_offset + 1L)

      text_range <- list(
        startLine = line,
        endLine = line,
        startColumn = start_offset,
        endColumn = end_offset
      )
    }
  }

  issues[[length(issues) + 1]] <- list(
    engineId = "lintr",
    ruleId = as.character(lint$linter),
    severity = "MINOR",
    type = "CODE_SMELL",
    primaryLocation = list(
      message = as.character(lint$message),
      filePath = filename,
      textRange = text_range
    )
  )
}

jsonlite::write_json(list(issues = issues), path = out_json, auto_unbox = TRUE, pretty = TRUE)
