$(document).ready(function () {
  $("table.table").DataTable({
    // Do not allow default sorting (on the first column)
    "order":[]
  });
})