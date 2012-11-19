/* App Module */

angular.module('YourAppName', [], function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
	$interpolateProvider.endSymbol('}]}');
});
