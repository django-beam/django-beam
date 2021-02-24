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
      "#id_" + that.prefix + "-" + itemId + "-" + that.orderFieldName
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
        this.items.length
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
          jQuery(this).closest(".related-inline-item").data("inline-id")
        );
      })
      .removeClass("d-none");
  }
  $elem.on("click", ".related-inline-item-add", function (event) {
    event.preventDefault();
    that.add();
  });
  $elem.find(".related-inline-item-add").removeClass("d-none");
  $elem.find(".related-inline-item-remove").removeClass("d-none");

  if (this.canOrder) {
    let group = $elem.find(".related-inline-group")[0];
    Sortable.create(group, {
      dataIdAttr: "data-inline-id",
      handle: ".handle",
      store: {
        get: function (sortable) {
          sortable.sort(that.getItemIdsInOrder());
        },
        set: function (sortable) {
          that.setItemOrderFromIds(sortable.toArray());
        },
      },
    });
  }

  this.render();
}

RelatedInline.prototype.getItemCount = function () {
  return this.items.length;
};

RelatedInline.prototype.render = function () {
  let itemCount = this.getItemCount();
  jQuery(this.numItemsInput).val(itemCount);

  for (let item of this.items) {
    if (item.elem === undefined) {
      let template = jQuery(this.elem).find(".empty-form")[0].outerHTML;
      let itemHtml = template.replace(/__prefix__/g, item.id);
      item.elem = jQuery(itemHtml)
        .removeClass("empty-form")
        .appendTo(jQuery(this.elem).find(".related-inline-group"))[0];
    }
    if (this.canOrder && item.orderInput === undefined) {
      item.orderInput = jQuery(item.elem).find(
        "#id_" + this.prefix + "-" + item.id + "-" + this.orderFieldName
      );
      jQuery(item.orderInput).closest(".field-group").children().hide();
      jQuery(item.orderInput)
        .closest(".field-group")
        .append(
          "<label class='handle col-form-label btn' style='cursor: grab'>↕</label>"
        );
    }
    if (this.canDelete && item.deleteInput === undefined) {
      jQuery(item.elem)
        .find('[name="' + this.prefix + "-" + item.id + '-DELETE"]')
        .closest(".beam-field-DELETE")
        .remove();
      item.deleteInput = jQuery(
        '<input type="hidden" name="' +
          this.prefix +
          "-" +
          item.id +
          '-DELETE">'
      )[0];
      jQuery(item.elem)
        .find(".related-inline-item-remove")
        .after(item.deleteInput);
    }

    if (item.deleted) {
      jQuery(item.elem).hide();
      jQuery(item.deleteInput).val(true);
    } else {
      jQuery(item.elem).show();
      jQuery(item.deleteInput).val(false);
    }
    if (this.canOrder) {
      jQuery(item.orderInput).val(item.order);
    }
  }
};

RelatedInline.prototype._addItem = function (itemId, elem, order) {
  let item = {
    id: itemId,
    elem: elem,
    order: order,
    orderInput: undefined,
    deleteInput: undefined,
    deleted: false,
  };
  this.items.push(item);
  return item;
};

RelatedInline.prototype.getNextItemId = function () {
  let maxId = -1;
  for (let item of this.items) {
    if (item.id >= maxId) {
      maxId = item.id;
    }
  }
  return maxId + 1;
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

RelatedInline.prototype.getItemIdsInOrder = function () {
  let sortedItems = this.items.slice();
  sortedItems.sort(function (a, b) {
    return a.order - b.order;
  });
  let ids = [];
  for (let item of sortedItems) {
    ids.push(item.id);
  }
  return ids;
};
RelatedInline.prototype.setItemOrderFromIds = function (ids) {
  for (let i = 0; i < ids.length; i++) {
    for (let item of this.items) {
      if (String(item.id) === String(ids[i])) {
        item.order = i;
        break;
      }
    }
  }
  this.render();
};

RelatedInline.prototype.add = function () {
  let itemId = this.getNextItemId();
  let order = this.getMaxOrder() + 1;
  let item = this._addItem(itemId, undefined, order);
  this.render();

  let event = new CustomEvent("formset:added", {
    detail: { elem: item.elem, prefix: this.prefix },
  });
  this.elem.dispatchEvent(event);
};

RelatedInline.prototype.remove = function (id) {
  let deleted;
  for (let item of this.items) {
    if (item.id === id) {
      item.deleted = true;
      deleted = item;
    }
  }
  this.render();

  if (deleted !== undefined) {
    let event = new CustomEvent("formset:removed", {
      detail: { elem: deleted.elem, prefix: this.prefix },
    });
    this.elem.dispatchEvent(event);
  }
};

jQuery(function () {
  jQuery("[data-related-inline-js]").each(function () {
    new RelatedInline(this);
  });
});
