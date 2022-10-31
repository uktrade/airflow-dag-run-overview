function getDropdownFilterComponent(options) {
  function DropdownFilterComponent() {}

  DropdownFilterComponent.prototype.init = function (params) {
    this.eGui = document.createElement("div");
    this.eGui.className = "ag-floating-filter-input";
    var html =
      '<div class="ag-labeled ag-label-align-left ag-text-field ag-input-field">' +
      '<div class="ag-wrapper ag-input-wrapper ag-text-field-input-wrapper">' +
      '<select class="state-filter"><option></option>';
    for (var i=0; i < options.length; i++) {
      html += '<option value="' + options[i] + '">' + options[i] + '</option>'
    }
    html += '</select></div></div>';
    this.eGui.innerHTML = html;
    this.currentValue = null;
    this.eFilterInput = this.eGui.querySelector("select");
    this.eFilterInput.style.color = params.color;
    var that = this;

    function onSelectChanged() {
      if (that.eFilterInput.value === "") {
        params.parentFilterInstance(function (instance) {
          instance.onFloatingFilterChanged(null, null);
        });
        return;
      }

      that.currentValue = that.eFilterInput.value;
      params.parentFilterInstance(function (instance) {
        instance.onFloatingFilterChanged("equals", that.currentValue);
      });
    }

    this.eFilterInput.addEventListener("input", onSelectChanged);
  };

  DropdownFilterComponent.prototype.onParentModelChanged = function (
    parentModel
  ) {
    if (!parentModel) {
      this.eFilterInput.value = "";
      this.currentValue = null;
    } else {
      this.eFilterInput.value = parentModel.filter + "";
      this.currentValue = parentModel.filter;
    }
  };

  DropdownFilterComponent.prototype.getGui = function () {
    return this.eGui;
  };

  return DropdownFilterComponent;
}

class LoadingOverlay {
  init(params) {
    this.eGui = document.createElement('div');
    this.eGui.innerHTML =
      '<div class="ag-overlay-loading-center">' +
      params.loadingMessage +
      ' </i>' +
      '</div>';
  }

  getGui() {
    return this.eGui;
  }

  refresh(params) {
    return false;
  }
}

function autoSizeColumns(columnApi) {
  var allColumnIds = [];
  columnApi.getAllColumns().forEach(function (column) {
    allColumnIds.push(column.colId);
  });
  columnApi.autoSizeColumns(allColumnIds, false);
}

function dateFilterComparator(filterDate, cellDate) {
  if (cellDate !== 'N/A') {
    filterDate = dayjs(filterDate);
    cellDate = dayjs(cellDate);
    if (cellDate < filterDate) {
      return -1;
    } else if (cellDate > filterDate) {
      return 1;
    }
    return 1
  }
  return 0;
}

function clearDags(dag_ids, callback) {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', "/droview/api/clear-dags", true);
  xhr.setRequestHeader('X-CSRFToken', csrfToken);
  xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  xhr.onreadystatechange = function() {
    if (this.readyState === XMLHttpRequest.DONE) {
      callback();
    }
  }
  xhr.send(JSON.stringify({dag_ids: dag_ids}));
}

function clearHighPriorityDags( callback) {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', "/droview/api/clear-failed-dags?tag=High%20Priority", true);
  xhr.setRequestHeader('X-CSRFToken', csrfToken);
  xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  xhr.onreadystatechange = function() {
    if (this.readyState === XMLHttpRequest.DONE) {
      callback();
    }
  }
  xhr.send();
}

function refreshGrid(gridOptions, callback) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', "/droview/api/latest-dag-runs", true);
  xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  xhr.onreadystatechange = function() {
    if (this.readyState === XMLHttpRequest.DONE) {
      var response = JSON.parse(xhr.responseText);
      for (var i=0; i<response.length; i++) {
        var dag = response[i];
        var rowNode = gridOptions.api.getRowNode(dag.dag_id);
        rowNode.setDataValue("labelStyle", dag.label_style);
        rowNode.setDataValue("state", dag.state);
        rowNode.setDataValue("endDate", "N/A");
      }
      gridOptions.api.refreshCells()
      callback();
    }
  }
  xhr.send();
}

function initToolbar(gridOptions) {
  // Clear selected
  document.getElementById("clear-selected").addEventListener("click", function(e) {
    e.preventDefault();
    gridOptions.api.showLoadingOverlay();
    var selectedNodes = gridOptions.api.getSelectedNodes();
    var dagIds = [];
    for (var i=0; i<selectedNodes.length; i++) {
      dagIds.push(selectedNodes[i].data.dagId);
    }
    clearDags(dagIds, function() {
      refreshGrid(gridOptions, function () {
        gridOptions.api.hideOverlay();
      });
    });
  });

  // Refresh grid
  document.getElementById("refresh").addEventListener("click", function(e) {
    e.preventDefault();
    gridOptions.api.showLoadingOverlay();
    refreshGrid(gridOptions, function () {
      gridOptions.api.hideOverlay();
    });
  });

  // Clear all failed high priority pipelines
  document.getElementById("clear-high-priority").addEventListener("click", function(e) {
    e.preventDefault();
    gridOptions.api.showLoadingOverlay();
    clearHighPriorityDags(function() {
      refreshGrid(gridOptions, function () {
        gridOptions.api.hideOverlay();
      });
    });
  });
}

function initDataGrid(rowData, stateFilter, tagFilter) {
  var gridOptions = {
    suppressRowClickSelection: true,
    rowSelection: 'multiple',
    defaultColDef: {
      resizable: true,
      suppressMenu: true,
      floatingFilter: true,
      sortable: true,
      filter: true,
      dataType: "text"
    },
    filterParams: {
      suppressAndOrCondition: true,
      buttons: ['reset']
    },
    getRowId: (params) => {
      return params.data.dagId;
    },
    columnDefs: [{
      field: "dagId",
      headerName: "DAG",
      cellRenderer: function(cellData) {
        return '<a href="/dags/' + cellData.getValue() + '/graph">' + cellData.getValue() + '<a>';
      },
      headerCheckboxSelection: true,
      headerCheckboxSelectionFilteredOnly: true,
      checkboxSelection: true,
    }, {
      field: "scheduleInterval",
      headerName: "Schedule",
      filter: false,
      cellRenderer: function(cellData) {
        return '<span class="label label-default schedule">' + cellData.getValue() + '</span>';
      }
    }, {
      field: "startDate",
      headerName: "Started",
      filter: false,
      filterParams: {
        comparator: dateFilterComparator
      }
    }, {
      field: "endDate",
      headerName: "Finished",
      filter: false,
      filterParams: {
        comparator: dateFilterComparator
      }
    }, {
      field: "state",
      headerName: "Status",
      floatingFilterComponent: "stateFloatingFilter",
      floatingFilterComponentParams: {
        suppressFilterButton: true
      },
      cellRenderer: function(cellData) {
        var styles = cellData.data.labelStyle;
        return '<span class="label" style="border: none; background-color:' + styles.background + ';color:' + styles.foreground + '">' + cellData.getValue() + '</span>';
      }
    }, {
      field: "priority",
      headerName: "Priority",
      floatingFilterComponent: "highProfileFloatingFilter",
      floatingFilterComponentParams: {
        suppressFilterButton: true
      },
      cellRenderer: function(cellData) {
        if (cellData.data.priority === "high") {
          return '<span class="text-danger" title="High priority">' +
                '<span class="material-icons" aria-hidden="true">error</span>' +
                '&nbsp;High'
            '</span>';
        }
        return "";
      }
    }, {
      field: "actions",
      filter: false,
      sortable: false,
      cellRenderer: function (cellData) {
        var buttonWrap = document.createElement("div");
        buttonWrap.className = "action-button-wrap";
        var playButton = document.createElement("a");
        playButton.href = "#";
        playButton.title = "Rerun this DAG";
        playButton.innerHTML = '<span class="material-icons" aria-hidden="true">play_arrow</span>'
        playButton.onclick = function(e) {
          e.preventDefault();
          gridOptions.api.showLoadingOverlay();
          clearDags([cellData.data.dagId], function() {
            refreshGrid(gridOptions, function() {
              gridOptions.api.hideOverlay();
            });
          });
        }
        buttonWrap.append(playButton)
        if (cellData.data.logUrl != null) {
          var viewLogButton = document.createElement("a");
          viewLogButton.href = cellData.data.logUrl;
          viewLogButton.title = "View pipline logs";
          viewLogButton.target = "__blank";
          viewLogButton.innerHTML = '<span class="material-icons" aria-hidden="true">list</span>'
          buttonWrap.append(viewLogButton);
        }
        return buttonWrap;
      }
    }, {
      field: "labelStyle",
      hide: true,
      suppressToolPanel: true
    }],
    rowData: rowData,
    components: {
      stateFloatingFilter: getDropdownFilterComponent(["running", "failed", "success"]),
      highProfileFloatingFilter: getDropdownFilterComponent(["high"]),
    },
    loadingOverlayComponent: LoadingOverlay,
    loadingOverlayComponentParams: {
      loadingMessage: 'Loading...',
    },
    onSelectionChanged: function(event) {
      var rowCount = event.api.getSelectedNodes().length;
      var btn = document.getElementById("clear-selected");
      if (rowCount > 0) {
        btn.removeAttribute("disabled");
      }
      else {
        btn.setAttribute("disabled", "disabled");
      }
    },
    onGridReady: function() {
      var filterModel = {};
      if (stateFilter !== null) {
        filterModel.state = {
          filterType: 'text',
          type: 'equals',
          filter: stateFilter
        };
      }
      if (tagFilter !== null) {
        console.log('TAG FILTER', tagFilter);
        filterModel.priority = {
          filterType: 'text',
          type: 'equals',
          filter: tagFilter
        };
      }
      gridOptions.api.setFilterModel(filterModel);
      initToolbar(gridOptions);
      autoSizeColumns(gridOptions.columnApi);
    },
  };
  var gridContainer = document.querySelector('#dag-grid');
  new agGrid.Grid(gridContainer, gridOptions);
}

window.initDataGrid = initDataGrid;
