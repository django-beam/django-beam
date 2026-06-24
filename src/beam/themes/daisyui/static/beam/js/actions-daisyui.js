jQuery(document).ready(function ($) {
  // Action choice handler
  $(".beam-action__choice").on("change", function () {
    var form = $(this).closest("form");
    // hide all action forms but the one required for the current action on select
    form.find(".beam-action-form").addClass("hidden"); // Changed from hide() to addClass("hidden")
    if (this.value !== "_no_action_selected") {
      form.find("#beam-action-form-" + this.value).removeClass("hidden"); // Changed from show() to removeClass("hidden")
    }
  });

  // Select all/none functionality
  function updateActionUI() {
    var form = $("form[id$='-action-form'], #list-action-form");
    var selectedItems = form.find(".beam-action__select-item:checked");
    var allItems = form.find(".beam-action__select-item");
    var selectedItemsText = form.find(".beam-action__selected-items-text");
    var selectAcrossButton = form.find(".beam-action__select-across-button");
    var cancelSelectionButton = form.find(
      ".beam-action__clear-selection-button",
    );

    if (selectedItems.length > 0) {
      var textTemplate = selectedItemsText.data("text-template");
      var text = textTemplate
        .replace("COUNT", selectedItems.length)
        .replace("TOTAL", allItems.length);
      selectedItemsText.text(text).removeClass("hidden"); // Changed from show() to removeClass("hidden")

      if (selectedItems.length === allItems.length) {
        var selectAcrossTextTemplate = selectAcrossButton.data("text-template");
        var selectAcrossText = selectAcrossTextTemplate.replace(
          "TOTAL",
          allItems.length,
        );
        selectAcrossButton.text(selectAcrossText).removeClass("hidden"); // Changed from show() to removeClass("hidden")
      } else {
        selectAcrossButton.addClass("hidden"); // Changed from hide() to addClass("hidden")
      }
      cancelSelectionButton.removeClass("hidden"); // Changed from show() to removeClass("hidden")
    } else {
      selectedItemsText.addClass("hidden"); // Changed from hide() to addClass("hidden")
      selectAcrossButton.addClass("hidden"); // Changed from hide() to addClass("hidden")
      cancelSelectionButton.addClass("hidden"); // Changed from hide() to addClass("hidden")
    }
  }

  // Select all checkbox handler
  $(".beam-action__select-all").on("change", function () {
    var form = $(this).closest("form");
    var isChecked = $(this).prop("checked");

    form.find(".beam-action__select-item").each(function () {
      $(this).prop("checked", isChecked);
    });

    updateActionUI();
  });

  // Individual item checkbox handler
  $(document).on("change", ".beam-action__select-item", function () {
    var form = $(this).closest("form");
    var selectedItems = form.find(".beam-action__select-item:checked");
    var allItems = form.find(".beam-action__select-item");
    var selectAllCheckbox = form.find(".beam-action__select-all");

    // Update select all checkbox state
    if (selectedItems.length === allItems.length) {
      selectAllCheckbox.prop("checked", true);
      selectAllCheckbox.prop("indeterminate", false);
    } else if (selectedItems.length === 0) {
      selectAllCheckbox.prop("checked", false);
      selectAllCheckbox.prop("indeterminate", false);
    } else {
      selectAllCheckbox.prop("checked", false);
      selectAllCheckbox.prop("indeterminate", true);
    }

    updateActionUI();
  });

  // Select across button handler
  $(".beam-action__select-across-button").on("click", function (e) {
    e.preventDefault();
    var form = $(this).closest("form");
    form.find(".beam-action__select-across").val("1");
    updateActionUI();
  });

  // Clear selection button handler
  $(".beam-action__clear-selection-button").on("click", function (e) {
    e.preventDefault();
    var form = $(this).closest("form");
    form.find(".beam-action__select-item").prop("checked", false);
    form.find(".beam-action__select-all").prop("checked", false);
    form.find(".beam-action__select-across").val("");
    updateActionUI();
  });

  // Initialize UI on page load
  updateActionUI();
});
