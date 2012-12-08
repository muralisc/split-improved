/* App Module */
//replace the angular js markers as they conflict with Django template markers
angular.module('YourAppName', [], function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
	$interpolateProvider.endSymbol('}]}');
});
