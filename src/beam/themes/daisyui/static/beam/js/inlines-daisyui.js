function RelatedInline(elem) {
  this.elem = elem;
  this.items = [];
  let $elem = jQuery(elem);
  this.canOrder = !!$elem.data("can-order");
  this.canDelete = !!$elem.data("can-delete");
  this.orderFieldName = $elem.data("order-field");
  this.prefix = $elem.data("prefix");
  this.numItemsInput = $elem.find("#id_" + this.prefix + "-TOTAL_FORMS")[0];

  let that = this;

  $elem.find(".related-inline-group .related-inline-item").each(function () {
    let itemId = jQuery(this).data("inline-id");
    let orderInput = jQuery(this).find(
      "#id_" + that.prefix + "-" + itemId + "-" + that.orderFieldName,
    );
    let order = parseInt(jQuery(orderInput).val(), 10);
    // might result in invalid order values, fixed after all items are added
    that._addItem(itemId, this, order);
  });

  if (parseInt(this.numItemsInput.value, 10) !== this.items.length) {
    console.warn(
      "formset management form count " +
        this.numItemsInput.value +
        " does not match number of found inline items " +
        this.items.length,
    );
  }

  // fix missing order values from empty forms
  for (let item of this.items) {
    if (isNaN(item.order)) {
      item.order = this.getMaxOrder() + 1;
    }
  }

  if (this.canDelete) {
    $elem
      .on("click", ".related-inline-item-remove", function (event) {
        event.preventDefault();
        that.remove(
          jQuery(this).closest(".related-inline-item").data("inline-id"),
        );
      })
      .removeClass("hidden"); // Changed from d-none to hidden
  }
  $elem.on("click", ".related-inline-item-add", function (event) {
    event.preventDefault();
    that.add();
  });

  // Show add and remove buttons (changed from removeClass d-none to removeClass hidden)
  $elem.find(".related-inline-item-add").removeClass("hidden");
  $elem.find(".related-inline-item-remove").removeClass("hidden");

  if (this.canOrder) {
    // Add sortable functionality
    let sortableOptions = {
      handle: ".drag-handle", // You might want to add drag handles to your template
      animation: 150,
      onEnd: function (event) {
        that._reorderItems();
      },
    };

    if (typeof Sortable !== "undefined") {
      new Sortable($elem.find(".related-inline-group")[0], sortableOptions);
    }
  }

  this._reorderItems();
}

RelatedInline.prototype.add = function () {
  let itemId = parseInt(this.numItemsInput.value, 10);
  let emptyForm = jQuery(this.elem).find(".empty-form").first();
  let newForm = emptyForm.clone(true);

  // Replace __prefix__ with actual item id
  let html = newForm.html();
  html = html.replace(/__prefix__/g, itemId);
  newForm.html(html);
  newForm.removeClass("empty-form hidden"); // Changed from d-none to hidden
  newForm.attr("data-inline-id", itemId);
  newForm.attr("id", this.prefix + "-" + itemId);

  // Insert the new form
  emptyForm.parent().before(newForm);

  // Update the total forms count
  this.numItemsInput.value = itemId + 1;

  // Add to our items array
  let orderInput = newForm.find(
    "#id_" + this.prefix + "-" + itemId + "-" + this.orderFieldName,
  );
  this._addItem(itemId, newForm[0], this.getMaxOrder() + 1);

  this._reorderItems();
};

RelatedInline.prototype.remove = function (itemId) {
  let item = this._getItem(itemId);
  if (!item) return;

  // Mark for deletion or actually remove
  let deleteInput = jQuery(item.elem).find('input[name$="-DELETE"]');
  if (deleteInput.length) {
    // Mark for deletion
    deleteInput.val("on");
    jQuery(item.elem).hide(); // Hide the item
  } else {
    // Actually remove from DOM
    jQuery(item.elem).remove();
    // Update total forms count
    this.numItemsInput.value = parseInt(this.numItemsInput.value, 10) - 1;
  }

  // Remove from our items array
  this.items = this.items.filter((i) => i.id !== itemId);
  this._reorderItems();
};

RelatedInline.prototype._addItem = function (id, elem, order) {
  let orderInput = jQuery(elem).find(
    "#id_" + this.prefix + "-" + id + "-" + this.orderFieldName,
  );

  this.items.push({
    id: id,
    elem: elem,
    order: order,
    orderInput: orderInput[0],
  });
};

RelatedInline.prototype._getItem = function (itemId) {
  return this.items.find((item) => item.id == itemId);
};

RelatedInline.prototype.getMaxOrder = function () {
  let maxOrder = 0;
  for (let item of this.items) {
    if (!isNaN(item.order) && item.order > maxOrder) {
      maxOrder = item.order;
    }
  }
  return maxOrder;
};

RelatedInline.prototype._reorderItems = function () {
  if (!this.canOrder) return;

  // Sort items by their current position in the DOM
  let that = this;
  let sortedItems = [];

  jQuery(this.elem)
    .find(".related-inline-group .related-inline-item")
    .each(function (index) {
      let itemId = jQuery(this).data("inline-id");
      let item = that._getItem(itemId);
      if (item) {
        item.order = index + 1;
        if (item.orderInput) {
          jQuery(item.orderInput).val(item.order);
        }
        sortedItems.push(item);
      }
    });

  this.items = sortedItems;
};

// Initialize all related inlines when the document is ready
jQuery(document).ready(function () {
  jQuery("[data-related-inline-js]").each(function () {
    new RelatedInline(this);
  });
});
