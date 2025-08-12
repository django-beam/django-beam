jQuery(function () {
  // hide all action forms but the one required for the current action on select
  function revealCurrentActionForm() {
    let form = jQuery(this).closest("form");
    form.find(".beam-action-form").hide();
    form.find("#beam-action-form-" + this.value).show();
  }
  jQuery(".beam-action__choice")
    .change(revealCurrentActionForm)
    .each(revealCurrentActionForm);

  // ensure that changing the "select all" checkbox also changes all the checkboxes below
  function toggleSelectOnSelectAll() {
    let form = jQuery(this).closest("form");
    let inputs = form.find(".beam-action__select-item");
    inputs.prop("checked", jQuery(this).is(":checked"));
  }

  // update the selection / cancel / status texts and buttons at the top
  function updateSelectionTextsAndButtons() {
    let form = jQuery(this).closest("form");
    let items = form.find(".beam-action__select-item");
    let total = items.length;
    let checked = items.filter(":checked").length;
    let totalAcrossPages = form
      .find("[data-object-count]")
      .data("object-count");
    let selectAcrossActive =
      form.find(".beam-action__select-across").val() === "all";

    if (selectAcrossActive) {
      checked = totalAcrossPages;
      total = totalAcrossPages;
    }

    // we are using text supplied via data-text-template because
    // integrating djangos jsi18n with webpack & co is a pain
    // and our goal is to make integration of beam as easy as possible
    let selectedItemsText = form.find(".beam-action__selected-items-text");
    selectedItemsText.text(
      selectedItemsText
        .data("text-template")
        .replace("COUNT", checked)
        .replace("TOTAL", total),
    );
    selectedItemsText.show();

    let selectAcrossButton = form.find(".beam-action__select-across-button");
    if (checked === total && totalAcrossPages > total && !selectAcrossActive) {
      selectAcrossButton.text(
        selectAcrossButton
          .data("text-template")
          .replace("TOTAL", totalAcrossPages),
      );
      selectAcrossButton.show();
    } else {
      selectAcrossButton.hide();
    }

    let cancelSelectionButton = form.find(
      ".beam-action__clear-selection-button",
    );
    if (selectAcrossActive) {
      cancelSelectionButton.show();
    } else {
      cancelSelectionButton.hide();
    }
  }
  jQuery(".beam-action__select-across-button").click(function (e) {
    e.preventDefault();
    let form = jQuery(e.target).closest("form");
    form.find(".beam-action__select-across").val("all");
    updateSelectionTextsAndButtons.apply(form);
  });

  jQuery(".beam-action__clear-selection-button").click(function (e) {
    e.preventDefault();
    let form = jQuery(e.target).closest("form");
    form.find(".beam-action__select-across").val("");
    form.find(".beam-action__select-item").prop("checked", false);
    form.find(".beam-action__select-all").prop("checked", false);
    updateSelectionTextsAndButtons.apply(form);
  });

  jQuery("input.beam-action__select-item").change(
    updateSelectionTextsAndButtons,
  );
  jQuery("input.beam-action__select-all")
    .change(toggleSelectOnSelectAll)
    .change(updateSelectionTextsAndButtons)
    .each(updateSelectionTextsAndButtons)
    .each(toggleSelectOnSelectAll);
});
