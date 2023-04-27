function add_create_related_button(elem, text, url) {
  // ensure that in tables the button is positioned correctly
  if (elem.tagName === "TD") {
    elem.style.position = "relative";
    elem.style.paddingRight = "16px";
  }

  jQuery("<a><i class='fa fa-plus-circle' title='" + text + "'></a>")
    .appendTo(elem)
    .attr("rel", "opener")
    .attr("href", url)
    .attr("target", "_blank")
    .css({
      position: "absolute",
      right: 0,
      top: "6px",
    });
}

function change_input_value(elem, value, text) {
  if (elem.tagName === "SELECT") {
    let option = new Option(text, value, true, true);
    elem.appendChild(option);
  } else {
    elem.val(value);
  }
}

function handle_message_from_related(event) {
  let data = event.data;
  if (data.result === "created") {
    let id = data.id;
    let source = data.source;
    let text = data.text;
    let elem = document.getElementById(source);
    change_input_value(elem, id, text);
  }
}

jQuery(function () {
  window.addEventListener("message", handle_message_from_related, false);
  // FIXME right now this won't work for dynamically added inputs
  jQuery("[data-create-url]").each(function (index, elem) {
    add_create_related_button(
      elem,
      jQuery(elem).data("create-text"),
      jQuery(elem).data("create-url"),
    );
  });
});
