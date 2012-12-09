    function TimeFilterController($scope) {
		//function called to call prefefined timeranges
		$scope.showExpenseList = function() {
			switch($scope.timeRange){
				case "1":
					window.location.href = "?tr=1";
					break;
				case "2":
					window.location.href = "?tr=2";
					break;
				default:
					return;
			};
		};
		//append query string 
		$scope.sentTimeRange = function() {
			$scope.queryString = "?";
			$scope.tsExist = ((new Date($scope.t_s)).toString() != "Invalid Date");
			$scope.teExist = ((new Date($scope.t_e)).toString() != "Invalid Date");
			if(!$scope.tsExist && !$scope.teExist){
				alert("enter valid date");
				return;
			}
			if($scope.tsExist && $scope.teExist){
				if((new Date($scope.t_s)) > (new Date($scope.t_e))){
					alert("start date is after the end date duffer");
					return;
				}
			}
			if($scope.tsExist){  
				$scope.queryString = $scope.queryString.concat("ts=");
				$scope.queryString = $scope.queryString.concat($scope.t_s);
				$scope.queryString = $scope.queryString.concat("&");
			}
			if($scope.teExist){  
				$scope.queryString = $scope.queryString.concat("te=");
				$scope.queryString = $scope.queryString.concat($scope.t_e);
				$scope.queryString = $scope.queryString.concat("&");
			}
			window.location.href = $scope.queryString;
		};
	};
