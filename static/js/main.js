// Main JavaScript for Data Analytics Dashboard

document.addEventListener("DOMContentLoaded", () => {
  // File upload drag and drop functionality
  const uploadArea = document.querySelector(".upload-area")
  const fileInput = document.querySelector("#file")

  if (uploadArea && fileInput) {
    uploadArea.addEventListener("click", () => {
      fileInput.click()
    })

    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault()
      uploadArea.classList.add("border-primary")
    })

    uploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault()
      uploadArea.classList.remove("border-primary")
    })

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault()
      uploadArea.classList.remove("border-primary")

      const files = e.dataTransfer.files
      if (files.length > 0) {
        fileInput.files = files
        updateFileLabel(files[0].name)
      }
    })

    fileInput.addEventListener("change", function () {
      if (this.files.length > 0) {
        updateFileLabel(this.files[0].name)
      }
    })
  }

  function updateFileLabel(filename) {
    const uploadArea = document.querySelector(".upload-area p")
    if (uploadArea) {
      uploadArea.textContent = `Selected: ${filename}`
    }
  }

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert")
  const bootstrap = window.bootstrap // Declare the bootstrap variable
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert)
      bsAlert.close()
    }, 5000)
  })

  // Add loading state to buttons
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", () => {
      const submitBtn = form.querySelector('button[type="submit"]')
      if (submitBtn) {
        const originalText = submitBtn.innerHTML
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...'
        submitBtn.disabled = true

        // Re-enable button after 10 seconds as fallback
        setTimeout(() => {
          submitBtn.innerHTML = originalText
          submitBtn.disabled = false
        }, 10000)
      }
    })
  })

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Table search functionality
  const searchInput = document.querySelector("#tableSearch")
  if (searchInput) {
    searchInput.addEventListener("keyup", function () {
      const filter = this.value.toLowerCase()
      const table = document.querySelector("#data-table")
      const rows = table.querySelectorAll("tbody tr")

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase()
        row.style.display = text.includes(filter) ? "" : "none"
      })
    })
  }
})

// Utility functions
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return "0 Bytes"

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ["Bytes", "KB", "MB", "GB"]

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i]
}

function showNotification(message, type = "info") {
  const alertDiv = document.createElement("div")
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `

  const container = document.querySelector(".container")
  container.insertBefore(alertDiv, container.firstChild)

  // Auto dismiss after 5 seconds
  setTimeout(() => {
    const bsAlert = new window.bootstrap.Alert(alertDiv) // Use window.bootstrap
    bsAlert.close()
  }, 5000)
}
