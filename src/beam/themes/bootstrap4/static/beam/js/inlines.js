let $=jQuery

function RelatedInline(elem) {
    this.elem = elem
    this.items = []
    let $elem = $(elem)
    this.canOrder = !!$elem.data("can-order")
    this.canDelete = !!$elem.data("can-delete")
    this.orderFieldName = $elem.data("order-field")
    this.prefix = $elem.data("prefix")
    this.numItemsInput = $elem.find("#id_" + this.prefix + '-TOTAL_FORMS')[0]

    let that = this

    $elem.find(".related-inline-group .related-inline-item").each(function () {
        let itemId = $(this).data("inline-id")
        let orderInput = $(this).find("#id_" + that.prefix + "-" + itemId + "-" + that.orderFieldName)
        let order = parseInt($(orderInput).val(), 10)
        // might result in invalid order values, fixed after all items are added
        that._addItem(itemId, this, order)
    })

    // fix missing order values from empty forms
    for (let item of this.items) {
        if (isNaN(item.order)) {
            item.order = this.getMaxOrder() + 1
        }
    }

    if (this.canDelete) {
        $elem.on('click', '.related-inline-item-remove', function (event) {
            event.preventDefault()
            that.remove($(this).closest(".related-inline-item").data("inline-id"))
        }).removeClass("d-none")
    }
    $elem.on('click', '.related-inline-item-add', function (event) {
        event.preventDefault()
        that.add()
    })
    $elem.find(".related-inline-item-add").removeClass("d-none")
    $elem.find(".related-inline-item-remove").removeClass("d-none")

    if (this.canOrder) {
        let group = $elem.find('.related-inline-group')[0]
        Sortable.create(group, {
            dataIdAttr: "data-inline-id",
            handle: ".handle",
            store: {
                get: function (sortable) {
                    sortable.sort(that.getItemIdsInOrder())
                },
                set: function (sortable) {
                    that.setItemOrderFromIds(sortable.toArray())
                }
            }
        })
    }

    this.render()
}


RelatedInline.prototype.getItemCount = function () {
    return this.items.length;
}

RelatedInline.prototype.render = function () {
    let itemCount = this.getItemCount()
    $(this.numItemsInput).val(itemCount)

    for (let item of this.items) {
        if (item.elem === undefined) {
            let template = $(this.elem).find(".empty-form")[0].outerHTML
            let itemHtml = template.replace(/__prefix__/g, item.id)
            item.elem = $(itemHtml).removeClass("empty-form").appendTo($(this.elem).find('.related-inline-group'))[0]
        }
        if (this.canOrder && item.orderInput === undefined) {
            item.orderInput = $(item.elem).find("#id_" + this.prefix + "-" + item.id + "-" + this.orderFieldName)
            $(item.orderInput).closest(".field-group").children().hide()
            $(item.orderInput).closest(".field-group").append("<label class='handle col-form-label btn' style='cursor: grab'>↕</label>")
        }
        if (this.canDelete && item.deleteInput === undefined) {
            item.deleteInput = $('<input type="hidden" name="' + this.prefix + '-' + item.id + '-DELETE">').appendTo($(item.elem))[0]
        }

        if (item.deleted) {
            $(item.elem).hide()
            $(item.deleteInput).val(true)
        } else {
            $(item.elem).show()
            $(item.deleteInput).val(false)
        }
        if (this.canOrder) {
            $(item.orderInput).val(item.order)
        }
    }
}

RelatedInline.prototype._addItem = function (itemId, elem, order) {
    let item = {
        id: itemId,
        elem: elem,
        order: order,
        orderInput: undefined,
        deleteInput: undefined,
        deleted: false
    }
    this.items.push(item)
}

RelatedInline.prototype.getNextItemId = function () {
    let maxId = -1
    for (let item of this.items) {
        if (item.id >= maxId) {
            maxId = item.id
        }
    }
    return maxId + 1
}

RelatedInline.prototype.getMaxOrder = function () {
    let maxOrder = 0
    for (let item of this.items) {
        if (!isNaN(item.order) && item.order > maxOrder) {
            maxOrder = item.order
        }
    }
    return maxOrder
}

RelatedInline.prototype.getItemIdsInOrder = function () {
    let sortedItems = this.items.slice()
    sortedItems.sort(function (a, b) {
        return a.order - b.order
    })
    let ids = []
    for (let item of sortedItems) {
        ids.push(item.id)
    }
    return ids
}
RelatedInline.prototype.setItemOrderFromIds = function (ids) {
    for (let i = 0; i < ids.length; i++) {
        for (let item of this.items) {
            if (String(item.id) === String(ids[i])) {
                item.order = i
                break
            }
        }
    }
    this.render()
}

RelatedInline.prototype.add = function () {
    let itemId = this.getNextItemId()
    let order = this.getMaxOrder() + 1
    this._addItem(itemId, undefined, order)
    this.render()
}

RelatedInline.prototype.remove = function (id) {
    for (let item of this.items) {
        if (item.id === id) {
            item.deleted = true
        }
    }
    this.render()
}

$(function () {
    $("[data-related-inline-js]").each(function () {
        new RelatedInline(this)
    })
})
