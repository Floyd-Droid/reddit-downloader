$(document).ready(function () {
  let subTable = $("table.table").DataTable({
    // Do not allow default sorting
    "order":[]
  });

  // Inform the user that their search terms will be ignored if
  // 'controversial', 'rising', or 'random rising' is selected in praw_sort
  $("#id_praw_sort").change(function () {
    let p = this.parentNode;
    let options = ["controversial", "rising", "random_rising"];
    if (options.includes(this.value)) {
      if (!p.innerHTML.includes("<span")) {
        $("<span id='warning_message'>Search terms will be ignored for this option</span>").appendTo(p);
      }
    } else {
      // Remove warning message if a viable option is selected
      if (p.innerHTML.includes("<span")) {
        $("#warning_message").remove();
      }
    }
  });
})