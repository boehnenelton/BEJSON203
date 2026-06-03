/**
 * Test:         bejson_cache.test.js
 * Description:  Unit tests for the Field Map Cache in lib_bejson_core.js.
 */
const BEJSON = require('./lib_bejson_core.js');

function test_cache_lookup() {
    console.log("Running test_cache_lookup...");
    const doc = {
        Format_Version: "104",
        Fields: [{name: "id"}, {name: "name"}, {name: "value"}],
        Values: []
    };
    
    console.assert(BEJSON.bejson_core_get_field_index(doc, "name") === 1, "Field 'name' index should be 1");
    console.assert(BEJSON.bejson_core_get_field_index(doc, "value") === 2, "Field 'value' index should be 2");
    console.assert(BEJSON.bejson_core_get_field_index(doc, "missing") === -1, "Missing field index should be -1");
}

function test_cache_collision() {
    console.log("Running test_cache_collision...");
    const doc1 = {Format_Version: "104", Fields: [{name: "a"}, {name: "b"}]};
    const doc2 = {Format_Version: "104", Fields: [{name: "b"}, {name: "a"}]};
    
    console.assert(BEJSON.bejson_core_get_field_index(doc1, "a") === 0, "Doc1 'a' index should be 0");
    console.assert(BEJSON.bejson_core_get_field_index(doc2, "a") === 1, "Doc2 'a' index should be 1");
}

try {
    test_cache_lookup();
    test_cache_collision();
    console.log("JS Tests Passed!");
} catch (e) {
    console.error("JS Tests Failed:", e);
    process.exit(1);
}
